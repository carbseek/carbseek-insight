#!/usr/bin/env python3
"""CarbSeek Insight 内容自动更新流水线

每周一/周五 08:00（北京时间）由 GitHub Actions 触发：
  1. 抓取 Google News RSS（免费无需密钥，失败时尝试 Bing News RSS）
  2. 关键词打分、去重、筛选 Top 12
  3. 可选：调用 Moonshot/Kimi API 撰写分析（配置仓库 Secret MOONSHOT_API_KEY 后启用）
  4. 渲染 template/index.template.html → index.html，并归档原始数据到 data/auto/

安全策略：抓取结果少于 3 条时放弃本次更新，避免用空内容覆盖线上页面。
仅使用 Python 标准库，无需安装任何依赖。

运行模式：
  python3 weekly_update.py            # 正式模式（CI 用）：抓取 → 渲染 → 更新 index.html
  python3 weekly_update.py --init     # 初始化模式：用默认内容渲染，新闻区显示待启动提示
  python3 weekly_update.py --offline-test  # 离线测试：用内置样例渲染到 /tmp/test_render.html
"""
import json
import os
import re
import sys
import html as htmllib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "template", "index.template.html")
DEFAULTS = os.path.join(ROOT, "template", "defaults.json")
OUTPUT = os.path.join(ROOT, "index.html")
ARCHIVE_DIR = os.path.join(ROOT, "data", "auto")
STATE = os.path.join(ARCHIVE_DIR, "state.json")

KEYWORDS = ["碳足迹", "产品碳足迹", "碳标签", "碳标识", "CBAM", "欧盟电池法规",
            "生命周期评价", "EPD 环境产品声明", "碳中和 政策", "碳足迹 数据库"]
CORE_KW = ["碳足迹", "碳标签", "碳标识", "LCA", "生命周期", "CBAM", "电池法",
           "EPD", "DPP", "碳中和", "碳达峰", "碳核算", "碳认证"]
INDUSTRY_KW = ["化工", "电子", "电气", "汽车", "电池", "出口", "欧盟",
               "纺织", "钢铁", "光伏", "锂电"]
TOP_N = 12
MIN_ITEMS = 3

CST = timezone(timedelta(hours=8))  # 北京时间


# ---------- 抓取 ----------
def fetch_rss(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CarbSeekBot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):
        src = it.find("source")
        items.append({
            "title": it.findtext("title", "").strip(),
            "link": it.findtext("link", "").strip(),
            "date": it.findtext("pubDate", "").strip(),
            "source": (src.text or "").strip() if src is not None else "",
        })
    return items


def fetch_all():
    items = []
    for kw in KEYWORDS:
        q = urllib.parse.quote(kw + " when:30d")
        urls = [
            "https://news.google.com/rss/search?q=" + q + "&hl=zh-CN&gl=CN&ceid=CN:zh",
            "https://www.bing.com/news/search?q=" + q + "&format=rss",
        ]
        for url in urls:
            try:
                items.extend(fetch_rss(url))
                break
            except Exception as e:
                print("  抓取失败 [%s]: %s" % (kw, e))
    return items


# ---------- 清洗与打分 ----------
def norm_title(t):
    # 去掉 Google News 标题尾部的 " - 媒体名"
    return re.sub(r"\s*[-–—]\s*[^-–—]+$", "", t).strip()


def score(t):
    s = 0
    for k in CORE_KW:
        if k in t:
            s += 3
    for k in INDUSTRY_KW:
        if k in t:
            s += 2
    if re.search(r"\d|GB|ISO|标准|认证", t):
        s += 1
    return s


def clean(items):
    seen, out = set(), []
    for it in items:
        t = norm_title(it["title"])
        if len(t) < 8 or t in seen:
            continue
        seen.add(t)
        it["title"] = t
        it["score"] = score(t)
        try:
            it["dt"] = parsedate_to_datetime(it["date"])
        except Exception:
            it["dt"] = datetime.now(timezone.utc)
        out.append(it)
    out.sort(key=lambda x: (x["score"], x["dt"]), reverse=True)
    return out[:TOP_N]


# ---------- LLM 分析（可选，配置了 MOONSHOT_API_KEY 才启用） ----------
def llm_analysis(items):
    key = os.environ.get("MOONSHOT_API_KEY", "").strip()
    if not key:
        return None
    news = "\n".join("%d. %s（%s）" % (i + 1, it["title"], it["source"])
                     for i, it in enumerate(items))
    prompt = (
        "你是碳产业分析师。根据以下本周碳足迹/碳标签领域新闻，输出 JSON：\n"
        '{"alert": "一句话本周动态摘要（100字内）", '
        '"advice": [{"priority": "P0/P1/P2", "direction": "研发方向", '
        '"basis": "依据（40字内）", "grade": "A/B/C"}，共5条], '
        '"opportunities": [{"name": "产品/服务", "driver": "市场驱动力（40字内）", '
        '"heat": 1到3的整数}，共10条]}\n'
        "只输出 JSON，不要输出其他内容。\n\n新闻列表：\n" + news
    )
    body = json.dumps({
        "model": os.environ.get("LLM_MODEL", "kimi-k2-0905-preview"),
        "messages": [
            {"role": "system", "content": "你是碳产业分析师，只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://api.moonshot.cn/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            text = json.load(r)["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", text, re.S)
        data = json.loads(m.group(0))
        if not (data.get("alert") and len(data.get("advice", [])) >= 3
                and len(data.get("opportunities", [])) >= 5):
            return None
        return data
    except Exception as e:
        print("  LLM 分析失败，使用默认内容:", e)
        return None


# ---------- 渲染 ----------
def esc(s):
    return htmllib.escape(str(s), quote=True)


def news_rows(items):
    cls = {"高": "tag-red", "中": "tag-orange", "低": "tag-green"}
    rows = []
    for it in items:
        lv = "高" if it["score"] >= 5 else ("中" if it["score"] >= 3 else "低")
        rows.append(
            '                    <tr>\n'
            '                        <td><a class="news-link" href="%s" target="_blank" rel="noopener">%s</a></td>\n'
            '                        <td><span class="tag tag-blue">%s</span></td>\n'
            '                        <td>%s</td>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                    </tr>'
            % (esc(it["link"]), esc(it["title"]), esc(it["source"] or "资讯"),
               it["dt"].strftime("%Y-%m-%d"), cls[lv], lv))
    return "\n".join(rows)


def advice_rows(advice):
    pc = {"P0": "tag-red", "P1": "tag-orange", "P2": "tag-green"}
    gc = {"A": "tag-blue", "B": "tag-green", "C": "tag-orange"}
    rows = []
    for a in advice[:5]:
        rows.append(
            '                    <tr>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                        <td>%s</td>\n'
            '                        <td>%s</td>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                    </tr>'
            % (pc.get(a["priority"], "tag-green"), esc(a["priority"]),
               esc(a["direction"]), esc(a["basis"]),
               gc.get(a["grade"], "tag-orange"), esc(a["grade"])))
    return "\n".join(rows)


def opp_rows(opps):
    hc = {3: "tag-red", 2: "tag-orange", 1: "tag-green"}
    rows = []
    for i, o in enumerate(opps[:10], 1):
        heat = min(3, max(1, int(o.get("heat", 1))))
        rows.append(
            '                    <tr>\n'
            '                        <td>%d</td>\n'
            '                        <td>%s</td>\n'
            '                        <td>%s</td>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                    </tr>'
            % (i, esc(o["name"]), esc(o["driver"]), hc[heat], "🔥" * heat))
    return "\n".join(rows)


def load_json(path, fallback):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return fallback


def save_state(st):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def delta_text(cur, prev):
    if not prev:
        return "首期收录"
    d = (cur - prev) / prev * 100
    return "%s %.1f%% 较上期" % ("↑" if d >= 0 else "↓", abs(d))


def render(values):
    tpl = open(TEMPLATE, encoding="utf-8").read()
    for k, v in values.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", tpl)
    if left:
        raise RuntimeError("模板存在未填充 token: %s" % left)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(tpl)
    print("已生成 %s（%d 字节）" % (OUTPUT, len(tpl.encode("utf-8"))))


# ---------- 主流程 ----------
def week_tag(dt):
    y, w, _ = dt.isocalendar()
    return "WR-%d-W%02d" % (y, w)


def main():
    global OUTPUT
    now = datetime.now(CST)
    init_mode = "--init" in sys.argv
    offline = "--offline-test" in sys.argv
    defaults = load_json(DEFAULTS, {})

    if offline:
        items = [
            {"title": "测试：产品碳足迹标识认证试点扩容至多省市", "link": "https://example.com/1",
             "source": "测试源", "dt": now, "score": 6},
            {"title": "测试：CBAM 申报指南更新，钢铁下游产品追溯范围扩大", "link": "https://example.com/2",
             "source": "测试源", "dt": now, "score": 4},
            {"title": "测试：锂电池碳足迹背景数据库建设推进", "link": "https://example.com/3",
             "source": "测试源", "dt": now, "score": 5},
        ]
        OUTPUT = "/tmp/test_render.html"
    elif init_mode:
        items = []
    else:
        print("开始抓取情报...")
        items = clean(fetch_all())
        print("有效情报 %d 条" % len(items))
        if len(items) < MIN_ITEMS:
            print("抓取结果不足 %d 条，放弃本次更新（保留线上现有内容）" % MIN_ITEMS)
            return

    state = load_json(STATE, {})
    count = len(items)
    high = sum(1 for it in items if it["score"] >= 5)
    hot = min(99.0, round(50 + 1.2 * count + 2.5 * high, 1)) if count else 0

    analysis = None if init_mode else llm_analysis(items)
    if analysis:
        alert = esc(analysis["alert"])
        adv = advice_rows(analysis["advice"])
        opp = opp_rows(analysis["opportunities"])
        print("LLM 分析完成")
    else:
        if items:
            tops = "；".join(it["title"] for it in items[:2])
            alert = esc("本周收录碳产业情报 %d 条。重点关注：%s。" % (count, tops))
        else:
            alert = defaults.get("alert", "")
        adv = defaults.get("advice_rows", "")
        opp = defaults.get("opp_rows", "")

    if init_mode:
        nrow = ('                    <tr>\n'
                '                        <td colspan="4" style="color:var(--text-muted);text-align:center;padding:28px">'
                '首期自动更新将由 GitHub Actions 于周一/周五 08:00（北京时间）运行，届时此处展示最新抓取情报</td>\n'
                '                    </tr>')
        stat_count, stat_delta = "—", "等待首期自动更新"
        hot_index, hot_delta = "—", "等待首期自动更新"
        ncount = "待启动"
    else:
        nrow = news_rows(items)
        stat_count = str(count)
        stat_delta = delta_text(count, state.get("count"))
        hot_index = str(hot)
        hot_delta = delta_text(hot, state.get("hot"))
        ncount = str(count)

    render({
        "WEEK_TAG": week_tag(now),
        "STAT_COUNT": stat_count,
        "STAT_DELTA": stat_delta,
        "HOT_INDEX": hot_index,
        "HOT_DELTA": hot_delta,
        "ALERT_TEXT": alert,
        "NEWS_COUNT": ncount,
        "NEWS_ROWS": nrow,
        "ADVICE_ROWS": adv,
        "OPP_ROWS": opp,
        "UPDATE_DATE": now.strftime("%Y-%m-%d"),
    })

    if not init_mode and not offline:
        ts = now.strftime("%Y%m%d-%H%M")
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        with open(os.path.join(ARCHIVE_DIR, "weekly-%s.json" % ts), "w", encoding="utf-8") as f:
            json.dump({"week": week_tag(now), "generated_at": now.isoformat(), "items": items},
                      f, ensure_ascii=False, indent=2, default=str)
        save_state({"count": count, "hot": hot, "last_run": now.isoformat()})
        print("状态与归档已保存到 data/auto/")


if __name__ == "__main__":
    main()
