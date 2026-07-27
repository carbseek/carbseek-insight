#!/usr/bin/env python3
"""
CarbSeek Intelligence - Dashboard 生成器
=========================================
从SQLite数据库生成静态HTML Dashboard
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "carbseek_intel.db"
OUTPUT_DIR = Path(__file__).parent / "web"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_stats():
    """获取统计数据"""
    conn = get_db()
    c = conn.cursor()
    
    # 各类情报数量
    c.execute("SELECT source_type, COUNT(*) as count FROM articles GROUP BY source_type")
    source_stats = {r["source_type"]: r["count"] for r in c.fetchall()}
    
    # 今日新增
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) as count FROM articles WHERE date(collected_at) = ?", (today,))
    today_count = c.fetchone()["count"]
    
    # 本周新增
    c.execute("SELECT COUNT(*) as count FROM articles WHERE collected_at >= datetime('now', '-7 days')")
    week_count = c.fetchone()["count"]
    
    # 高价值情报
    c.execute("SELECT COUNT(*) as count FROM articles WHERE relevance_score >= 0.7")
    high_value = c.fetchone()["count"]
    
    # 政策倒计时
    c.execute("SELECT COUNT(*) as count FROM policies WHERE days_left <= 90 AND status = 'active'")
    urgent_policies = c.fetchone()["count"]
    
    conn.close()
    
    return {
        "total": sum(source_stats.values()),
        "today": today_count,
        "week": week_count,
        "high_value": high_value,
        "urgent_policies": urgent_policies,
        "by_source": source_stats,
    }


def get_articles(limit=50, source_type=None, industry=None, min_score=0.0):
    """获取情报列表"""
    conn = get_db()
    c = conn.cursor()
    
    query = """
        SELECT * FROM articles 
        WHERE relevance_score >= ?
    """
    params = [min_score]
    
    if source_type:
        query += " AND source_type = ?"
        params.append(source_type)
    
    if industry:
        query += " AND industry = ?"
        params.append(industry)
    
    query += " ORDER BY collected_at DESC LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    articles = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return articles


def get_policies():
    """获取政策倒计时"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM policies 
        WHERE status = 'active' 
        ORDER BY days_left ASC
    """)
    policies = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return policies


def get_weekly_report():
    """获取最新周报"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM weekly_reports ORDER BY generated_at DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def generate_dashboard_html():
    """生成Dashboard HTML"""
    stats = get_stats()
    articles = get_articles(limit=30)
    policies = get_policies()
    report = get_weekly_report()
    
    # 行业分布
    industries = {}
    for a in articles:
        ind = a.get("industry", "通用")
        industries[ind] = industries.get(ind, 0) + 1
    
    # 主题分布
    topics = {}
    for a in articles:
        topic = a.get("topic", "其他")
        if topic:
            topics[topic] = topics.get(topic, 0) + 1
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CarbSeek Intelligence | 碳足迹研发情报中心</title>
<style>
:root {{
  --bg: #0a0e17;
  --bg-card: #111827;
  --bg-hover: #1a2332;
  --border: #253044;
  --text: #e2e8f0;
  --text-secondary: #94a3b8;
  --green: #10b981;
  --blue: #3b82f6;
  --amber: #f59e0b;
  --red: #ef4444;
  --purple: #8b5cf6;
  --cyan: #06b6d4;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
}}

/* Header */
.header {{
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  padding: 16px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.header-inner {{
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.logo {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
}}
.logo-icon {{
  width: 36px; height: 36px;
  background: linear-gradient(135deg, var(--green), var(--cyan));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}}
.header-meta {{
  font-size: 13px;
  color: var(--text-secondary);
}}
.badge-live {{
  background: rgba(16, 185, 129, 0.15);
  color: var(--green);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}}

/* Stats Grid */
.stats-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  max-width: 1400px;
  margin: 24px auto;
  padding: 0 24px;
}}
.stat-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}}
.stat-value {{
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}}
.stat-label {{
  font-size: 13px;
  color: var(--text-secondary);
}}
.stat-total {{ color: var(--blue); }}
.stat-today {{ color: var(--green); }}
.stat-week {{ color: var(--purple); }}
.stat-high {{ color: var(--amber); }}
.stat-urgent {{ color: var(--red); }}

/* Main Layout */
.main {{
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px 40px;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}}

/* Cards */
.card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 20px;
}}
.card-header {{
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.card-title {{
  font-size: 15px;
  font-weight: 600;
}}
.card-body {{
  padding: 16px 20px;
}}

/* Article Item */
.article-item {{
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 12px;
}}
.article-item:last-child {{ border-bottom: none; }}
.article-badge {{
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  height: fit-content;
}}
.badge-news {{ background: rgba(59, 130, 246, 0.15); color: var(--blue); }}
.badge-academic {{ background: rgba(139, 92, 246, 0.15); color: var(--purple); }}
.badge-patent {{ background: rgba(6, 182, 212, 0.15); color: var(--cyan); }}
.badge-policy {{ background: rgba(239, 68, 68, 0.15); color: var(--red); }}
.badge-industry {{ background: rgba(16, 185, 129, 0.15); color: var(--green); }}

.article-content {{ flex: 1; }}
.article-title {{
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  line-height: 1.5;
}}
.article-summary {{
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 6px;
}}
.article-meta {{
  font-size: 11px;
  color: var(--text-secondary);
  display: flex;
  gap: 12px;
}}
.score-bar {{
  display: inline-block;
  width: 40px;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  vertical-align: middle;
  margin-left: 4px;
}}
.score-fill {{
  height: 100%;
  border-radius: 2px;
}}

/* Policy Countdown */
.countdown-item {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}}
.countdown-item:last-child {{ border-bottom: none; }}
.countdown-days {{
  width: 48px; height: 48px;
  border-radius: 10px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}}
.days-critical {{ background: rgba(239, 68, 68, 0.15); color: var(--red); }}
.days-high {{ background: rgba(245, 158, 11, 0.15); color: var(--amber); }}
.days-num {{ font-size: 16px; line-height: 1; }}
.days-label {{ font-size: 9px; margin-top: 2px; }}
.countdown-info {{ flex: 1; }}
.countdown-title {{ font-size: 13px; font-weight: 600; }}
.countdown-deadline {{ font-size: 11px; color: var(--text-secondary); }}

/* Source Distribution */
.source-bar {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.source-name {{
  width: 60px;
  font-size: 12px;
  color: var(--text-secondary);
}}
.source-track {{
  flex: 1;
  height: 8px;
  background: var(--bg);
  border-radius: 4px;
  overflow: hidden;
}}
.source-fill {{
  height: 100%;
  border-radius: 4px;
}}
.source-count {{
  width: 30px;
  font-size: 12px;
  text-align: right;
  color: var(--text-secondary);
}}

/* Weekly Report */
.judgment-box {{
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
}}
.judgment-label {{
  font-size: 12px;
  font-weight: 600;
  color: var(--blue);
  margin-bottom: 6px;
}}
.judgment-text {{
  font-size: 14px;
  line-height: 1.7;
}}

/* Tabs */
.tabs {{
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
  padding: 0 20px;
}}
.tab {{
  padding: 10px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}}
.tab:hover, .tab.active {{
  color: var(--blue);
  border-bottom-color: var(--blue);
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

@media (max-width: 1024px) {{
  .main {{ grid-template-columns: 1fr; }}
  .stats-grid {{ grid-template-columns: repeat(3, 1fr); }}
}}
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-inner">
    <div class="logo">
      <div class="logo-icon">🌿</div>
      <span>CarbSeek Intelligence</span>
    </div>
    <div class="header-meta">
      <span class="badge-live">● 实时追踪</span>
      <span>情报中心 v2.0 | {datetime.now().strftime('%Y-%m-%d')}</span>
    </div>
  </div>
</header>

<!-- Stats -->
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value stat-total">{stats['total']}</div>
    <div class="stat-label">总情报数</div>
  </div>
  <div class="stat-card">
    <div class="stat-value stat-today">{stats['today']}</div>
    <div class="stat-label">今日新增</div>
  </div>
  <div class="stat-card">
    <div class="stat-value stat-week">{stats['week']}</div>
    <div class="stat-label">本周新增</div>
  </div>
  <div class="stat-card">
    <div class="stat-value stat-high">{stats['high_value']}</div>
    <div class="stat-label">高价值情报</div>
  </div>
  <div class="stat-card">
    <div class="stat-value stat-urgent">{stats['urgent_policies']}</div>
    <div class="stat-label">紧急政策</div>
  </div>
</div>

<!-- Main Content -->
<div class="main">
  <!-- Left Column -->
  <div class="left-col">
'''

    # 一句话判断
    if report:
        html += f'''
    <div class="judgment-box">
      <div class="judgment-label">📊 本周一句话判断</div>
      <div class="judgment-text">{report.get('one_sentence_judgment', '暂无')}</div>
    </div>
'''

    # 情报列表
    html += '''
    <div class="card">
      <div class="card-header">
        <div class="card-title">📰 最新情报流</div>
        <span style="font-size:12px;color:#94a3b8">按相关度排序</span>
      </div>
      <div class="tabs">
        <div class="tab active">全部</div>
        <div class="tab">政策</div>
        <div class="tab">学术</div>
        <div class="tab">专利</div>
        <div class="tab">行业</div>
      </div>
      <div class="card-body">
'''

    badge_classes = {
        "news": "badge-news",
        "academic": "badge-academic",
        "patent": "badge-patent",
        "policy": "badge-policy",
        "industry": "badge-industry",
    }
    
    source_labels = {
        "news": "资讯", "academic": "学术", "patent": "专利",
        "policy": "政策", "industry": "行业"
    }
    
    for article in articles[:20]:
        badge = badge_classes.get(article["source_type"], "badge-news")
        label = source_labels.get(article["source_type"], article["source_type"])
        score = article.get("relevance_score", 0)
        score_width = int(score * 100)
        score_color = "#ef4444" if score >= 0.8 else "#f59e0b" if score >= 0.6 else "#3b82f6"
        
        html += f'''
        <div class="article-item">
          <span class="article-badge {badge}">{label}</span>
          <div class="article-content">
            <div class="article-title">{article["title"]}</div>
            <div class="article-summary">{article.get("summary", "")[:120]}...</div>
            <div class="article-meta">
              <span>{article.get("source", "")}</span>
              <span>{article.get("industry", "通用")}</span>
              <span>{article.get("publish_date", "")}</span>
              <span>相关度: {score:.2f}<span class="score-bar"><span class="score-fill" style="width:{score_width}%;background:{score_color}"></span></span></span>
            </div>
          </div>
        </div>
'''
    
    html += '''
      </div>
    </div>
  </div>

  <!-- Right Column -->
  <div class="right-col">
'''

    # 政策倒计时
    html += '''
    <div class="card">
      <div class="card-header">
        <div class="card-title">⏰ 政策倒计时</div>
      </div>
      <div class="card-body">
'''
    
    for policy in policies[:5]:
        days = policy.get("days_left", 0)
        days_class = "days-critical" if days <= 90 else "days-high"
        html += f'''
        <div class="countdown-item">
          <div class="countdown-days {days_class}">
            <span class="days-num">{days}</span>
            <span class="days-label">天</span>
          </div>
          <div class="countdown-info">
            <div class="countdown-title">{policy["title"]}</div>
            <div class="countdown-deadline">{policy.get("issuing_body", "")} | 截止: {policy.get("deadline_date", "")}</div>
          </div>
        </div>
'''
    
    html += '''
      </div>
    </div>
'''

    # 来源分布
    html += '''
    <div class="card">
      <div class="card-header">
        <div class="card-title">📊 情报来源分布</div>
      </div>
      <div class="card-body">
'''
    
    source_colors = {
        "news": "#3b82f6", "academic": "#8b5cf6", "patent": "#06b6d4",
        "policy": "#ef4444", "industry": "#10b981"
    }
    
    total = sum(stats["by_source"].values()) or 1
    for source, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
        pct = count / total * 100
        color = source_colors.get(source, "#3b82f6")
        label = source_labels.get(source, source)
        html += f'''
        <div class="source-bar">
          <span class="source-name">{label}</span>
          <div class="source-track">
            <div class="source-fill" style="width:{pct}%;background:{color}"></div>
          </div>
          <span class="source-count">{count}</span>
        </div>
'''
    
    html += '''
      </div>
    </div>
'''

    # 行业分布
    html += '''
    <div class="card">
      <div class="card-header">
        <div class="card-title">🏭 行业覆盖</div>
      </div>
      <div class="card-body">
'''
    
    for ind, count in sorted(industries.items(), key=lambda x: -x[1]):
        html += f'''
        <div class="source-bar">
          <span class="source-name">{ind}</span>
          <div class="source-track">
            <div class="source-fill" style="width:{count/max(industries.values())*100}%;background:#8b5cf6"></div>
          </div>
          <span class="source-count">{count}</span>
        </div>
'''
    
    html += '''
      </div>
    </div>
'''

    # 研发建议
    if report and report.get("rd_suggestions"):
        html += '''
    <div class="card">
      <div class="card-header">
        <div class="card-title">💡 研发建议</div>
      </div>
      <div class="card-body">
'''
        suggestions = json.loads(report["rd_suggestions"]) if isinstance(report["rd_suggestions"], str) else report["rd_suggestions"]
        for sug in suggestions[:5]:
            html += f'''
        <div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.6;">
          {sug}
        </div>
'''
        html += '''
      </div>
    </div>
'''

    html += '''
  </div>
</div>

<script>
// 简单的标签切换
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    this.classList.add('active');
  });
});
</script>

</body>
</html>
'''

    # 写入文件
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[Dashboard] 生成完成: {output_path}")
    print(f"[Dashboard]   情报总数: {stats['total']}")
    print(f"[Dashboard]   今日新增: {stats['today']}")
    print(f"[Dashboard]   高价值: {stats['high_value']}")
    
    return output_path


if __name__ == "__main__":
    generate_dashboard_html()
