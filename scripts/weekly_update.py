#!/usr/bin/env python3
"""CarbSeek Insight 内容自动更新流水线（Carbon Intelligence Analyst）

每日 09:00（北京时间）由 GitHub Actions 触发：
  1. 抓取 Google News RSS 中英文双语源（免费无需密钥，失败时尝试 Bing News RSS）
  2. 关键词打分、机构匹配（Carbon Trust / South Pole / SGS 等监测目标）、
     来源可信度分级（🟢官方权威 / 🟡行业媒体 / 🟠待核实）、去重筛选 Top 12
  3. 可选：调用 Moonshot/Kimi API 撰写分析（配置仓库 Secret MOONSHOT_API_KEY 后启用）
  4. 渲染 template/index.template.html → index.html
  5. 归档：原始数据 JSON + Markdown 情报简报 → data/auto/

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

# ---------- 监测关键词（中文 + 英文双语种） ----------
KEYWORDS_CN = ["碳足迹", "产品碳足迹", "碳标签", "碳标识", "CBAM", "欧盟电池法规",
               "生命周期评价", "EPD 环境产品声明", "碳中和 政策", "碳足迹 认证"]
KEYWORDS_EN = ["carbon footprint certification", "carbon label", "Carbon Trust",
               "South Pole carbon", "ClimatePartner", "ISO 14067",
               "product carbon footprint", "carbon credit standard"]

CORE_KW = ["碳足迹", "碳标签", "碳标识", "LCA", "生命周期", "CBAM", "电池法",
           "EPD", "DPP", "碳中和", "碳达峰", "碳核算", "碳认证",
           "carbon footprint", "carbon label", "carbon credit", "net zero",
           "ISO 14067", "PAS 2050", "certification"]
INDUSTRY_KW = ["化工", "电子", "电气", "汽车", "电池", "出口", "欧盟",
               "纺织", "钢铁", "光伏", "锂电", "battery", "steel", "solar"]

# ---------- 重点监测机构（命中即在情报中标注） ----------
ORG_WATCH = {
    "Carbon Trust": ["Carbon Trust", "碳信托"],
    "South Pole": ["South Pole", "南极公司"],
    "ClimatePartner": ["ClimatePartner", "Climate Partner", "气候伙伴"],
    "Carbon Footprint Ltd": ["Carbon Footprint Ltd"],
    "SGS": ["SGS", "通标标准"],
    "TÜV": ["TÜV", "TUV", "莱茵", "南德"],
    "BSI": ["BSI", "英国标准协会"],
    "CQC": ["CQC", "中国质量认证中心"],
    "中环联合": ["中环联合"],
    "Watershed": ["Watershed"],
    "Persefoni": ["Persefoni"],
    "Sweep": ["Sweep"],
    "CDP": ["CDP"],
    "SBTi": ["SBTi", "科学碳目标"],
}

# ---------- 来源可信度分级（🟢高 / 🟡中 / 🟠待核实） ----------
TIER_GREEN = ["新华", "人民网", "央视", "中国政府网", "生态环境部", "市场监管",
              "中国环境报", "gov", "europa", "European Commission", "ISO",
              "UNFCCC", "国家", "官方"]
TIER_YELLOW = ["Carbon Brief", "PR Newswire", "Business Wire", "Reuters", "路透",
               "Bloomberg", "彭博", "第一财经", "21世纪", "财新", "澎湃", "界面",
               "中国能源报", "北极星", "索比", "高工", "Environmental", "edie",
               "S&P Global", "Ecosystem Marketplace"]

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


def fetch_one(kw, lang):
    q = urllib.parse.quote(kw + " when:30d")
    if lang == "en":
        urls = [
            "https://news.google.com/rss/search?q=" + q + "&hl=en-US&gl=US&ceid=US:en",
            "https://www.bing.com/news/search?q=" + q + "&format=rss",
        ]
    else:
        urls = [
            "https://news.google.com/rss/search?q=" + q + "&hl=zh-CN&gl=CN&ceid=CN:zh",
            "https://www.bing.com/news/search?q=" + q + "&format=rss",
        ]
    for url in urls:
        try:
            return fetch_rss(url)
        except Exception as e:
            print("  抓取失败 [%s]: %s" % (kw, e))
    return []


def fetch_all():
    items = []
    for kw in KEYWORDS_CN:
        items.extend(fetch_one(kw, "cn"))
    for kw in KEYWORDS_EN:
        items.extend(fetch_one(kw, "en"))
    return items


# ---------- 清洗与打分 ----------
def norm_title(t):
    # 去掉 Google News 标题尾部的 " - 媒体名"
    return re.sub(r"\s*[-–—]\s*[^-–—]+$", "", t).strip()


def score(t):
    s = 0
    tl = t.lower()
    for k in CORE_KW:
        if k.lower() in tl:
            s += 3
    for k in INDUSTRY_KW:
        if k.lower() in tl:
            s += 2
    if re.search(r"\d|GB|ISO|标准|认证|certif|standard", tl):
        s += 1
    return s


def match_org(t):
    for name, aliases in ORG_WATCH.items():
        for a in aliases:
            if a.lower() in t.lower():
                return name
    return ""


def credibility(source):
    sl = (source or "").lower()
    for k in TIER_GREEN:
        if k.lower() in sl:
            return ("🟢 高", "tag-green")
    for k in TIER_YELLOW:
        if k.lower() in sl:
            return ("🟡 中", "tag-orange")
    return ("🟠 待核实", "tag-red")


def clean(items):
    seen, out = set(), []
    for it in items:
        t = norm_title(it["title"])
        if len(t) < 8 or t in seen:
            continue
        seen.add(t)
        it["title"] = t
        it["score"] = score(t)
        it["org"] = match_org(t)
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
        "你是碳产业分析师（Carbon Intelligence Analyst）。根据以下碳足迹/碳标签/碳认证领域新闻，输出 JSON：\n"
        '{"alert": "一句话动态摘要（100字内）", '
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
        org = (' <span class="tag tag-purple">🏢 %s</span>' % esc(it["org"])) if it.get("org") else ""
        cred, ccls = credibility(it["source"])
        rows.append(
            '                    <tr>\n'
            '                        <td><a class="news-link" href="%s" target="_blank" rel="noopener">%s</a>%s</td>\n'
            '                        <td><span class="tag tag-blue">%s</span></td>\n'
            '                        <td>%s</td>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                        <td><span class="tag %s">%s</span></td>\n'
            '                    </tr>'
            % (esc(it["link"]), esc(it["title"]), org, esc(it["source"] or "资讯"),
               it["dt"].strftime("%Y-%m-%d"), ccls, cred, cls[lv], lv))
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


# ---------- Markdown 情报简报（Carbon Intelligence Analyst 标准格式） ----------
def briefing_md(items, now):
    lines = [
        "# 🌿 CarbSeek 每日碳情报简报",
        "",
        "> 生成时间：%s（北京时间）· Carbon Intelligence Analyst 自动流水线"
        % now.strftime("%Y-%m-%d %H:%M"),
        "> 可信度：🟢 高（官方/权威源）｜🟡 中（行业/财经媒体）｜🟠 待核实",
        "",
        "---",
        "",
    ]
    for i, it in enumerate(items, 1):
        cred, _ = credibility(it["source"])
        lines += [
            "### 情报 %d ｜ %s" % (i, cred),
            "",
            "- **日期**：%s" % it["dt"].strftime("%Y-%m-%d"),
            "- **🏢 机构**：%s" % (it["org"] or "未匹配（泛行业情报）"),
            "- **🌍 来源**：%s" % (it["source"] or "资讯"),
            "- **【事件描述】** %s" % it["title"],
            "- **🔗 链接**：%s" % it["link"],
            "",
        ]
    lines += [
        "---",
        "",
        "> 配置仓库 Secret `MOONSHOT_API_KEY` 后，简报将追加【影响分析】与【战略启示】（对 CarbSeek / 对碳标签产业研究院）。",
    ]
    return "\n".join(lines)


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
             "source": "新华网", "dt": now, "score": 6, "org": "CQC"},
            {"title": "Test: Carbon Trust launches new product carbon footprint certification service",
             "link": "https://example.com/2", "source": "Carbon Brief", "dt": now,
             "score": 7, "org": "Carbon Trust"},
            {"title": "测试：锂电池碳足迹背景数据库建设推进", "link": "https://example.com/3",
             "source": "自媒体资讯", "dt": now, "score": 5, "org": ""},
        ]
        OUTPUT = "/tmp/test_render.html"
    elif init_mode:
        items = []
    else:
        print("开始抓取情报（中英双语 %d 组关键词）..." % (len(KEYWORDS_CN) + len(KEYWORDS_EN)))
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
            alert = esc("本期收录碳产业情报 %d 条。重点关注：%s。" % (count, tops))
        else:
            alert = defaults.get("alert", "")
        adv = defaults.get("advice_rows", "")
        opp = defaults.get("opp_rows", "")

    if init_mode:
        nrow = ('                    <tr>\n'
                '                        <td colspan="5" style="color:var(--text-muted);text-align:center;padding:28px">'
                '首期自动更新将由 GitHub Actions 于每日 09:00（北京时间）运行，届时此处展示最新抓取情报</td>\n'
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
        "ORG_ROWS": defaults.get("org_rows", ""),
        "MODEL_CARDS": defaults.get("model_cards", ""),
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
        with open(os.path.join(ARCHIVE_DIR, "briefing-%s.md" % ts), "w", encoding="utf-8") as f:
            f.write(briefing_md(items, now))
        save_state({"count": count, "hot": hot, "last_run": now.isoformat()})
        print("状态、归档与 Markdown 简报已保存到 data/auto/")


if __name__ == "__main__":
    main()
