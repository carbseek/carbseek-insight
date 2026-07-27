#!/usr/bin/env python3
"""
CarbSeek Intelligence - Orchestrator 总控调度器
===============================================
负责：拆任务、调度Agent、去重、评分、生成周报
"""
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 导入所有Agent
sys.path.insert(0, str(Path(__file__).parent / "agents"))
from baidu_news_agent import BaiduNewsAgent
from cnki_agent import CNKIAgent
from patent_agent import PatentAgent
from industry_agent import IndustryAgent
from policy_agent import PolicyAgent

sys.path.insert(0, str(Path(__file__).parent / "database"))
from init_db import get_connection


class Orchestrator:
    """情报中心总控调度器"""
    
    def __init__(self):
        self.agents = {
            "news": BaiduNewsAgent(),
            "academic": CNKIAgent(),
            "patent": PatentAgent(),
            "industry": IndustryAgent(),
            "policy": PolicyAgent(),
        }
        
        self.keywords = [
            "碳足迹", "碳标签", "碳标识", "产品碳足迹", "碳认证",
            "CBAM", "欧盟电池法规", "碳边境",
            "LCA", "生命周期评价", "Scope 3", "范围三",
            "EPD", "PCR", "碳核算", "碳数据平台"
        ]
        
        self.industries = ["电气电子", "化工", "汽车", "欧盟出口", "通用"]
    
    def run_all_agents(self) -> List[Dict]:
        """运行所有Agent采集情报"""
        print(f"\n{'='*60}")
        print(f"[Orchestrator] 启动全量情报采集")
        print(f"[Orchestrator] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        results = []
        
        for name, agent in self.agents.items():
            try:
                result = agent.run(self.keywords)
                results.append(result)
            except Exception as e:
                print(f"[Orchestrator] ✗ {name} 异常: {str(e)}")
                results.append({
                    "agent": name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def generate_weekly_report(self) -> Dict:
        """生成周报"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # 获取本周数据
        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 统计
        cursor.execute("""
            SELECT source_type, COUNT(*) as count 
            FROM articles 
            WHERE collected_at >= ?
            GROUP BY source_type
        """, (week_start,))
        
        stats = {row["source_type"]: row["count"] for row in cursor.fetchall()}
        
        # 高价值文章
        cursor.execute("""
            SELECT * FROM articles 
            WHERE relevance_score >= 0.6 

            ORDER BY relevance_score DESC, collected_at DESC
            LIMIT 10
        """)
        
        top_articles = [dict(row) for row in cursor.fetchall()]
        
        # 政策倒计时
        cursor.execute("""
            SELECT * FROM policies 
            WHERE status = 'active' AND days_left <= 180
            ORDER BY days_left ASC
        """)
        
        policies = [dict(row) for row in cursor.fetchall()]
        
        # 生成周报数据
        week_num = int(datetime.now().strftime("%W"))
        year = datetime.now().year
        report_id = f"WR-{year}-W{week_num:02d}"
        
        report = {
            "report_id": report_id,
            "week_start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "week_end": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            
            "stats": {
                "total_articles": sum(stats.values()),
                "by_source": stats,
            },
            
            "one_sentence_judgment": self._generate_judgment(top_articles, policies),
            
            "top_articles": top_articles,
            
            "policy_countdown": policies,
            
            "key_changes": self._extract_key_changes(top_articles),
            
            "opportunities": self._extract_opportunities(top_articles),
            
            "risks": self._extract_risks(policies),
            
            "impact": {
                "pro": self._impact_on_pro(top_articles, policies),
                "scan": self._impact_on_scan(top_articles),
                "db": self._impact_on_db(top_articles),
            },
            
            "rd_suggestions": self._generate_rd_suggestions(top_articles, policies),
        }
        
        # 保存到数据库
        cursor.execute("""
            INSERT OR REPLACE INTO weekly_reports 
            (report_id, week_start, week_end, one_sentence_judgment,
             key_changes, opportunities, risks, article_count, patent_count, policy_count,
             impact_pro, impact_scan, impact_db, rd_suggestions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["report_id"],
            report["week_start"],
            report["week_end"],
            report["one_sentence_judgment"],
            json.dumps(report["key_changes"], ensure_ascii=False),
            json.dumps(report["opportunities"], ensure_ascii=False),
            json.dumps(report["risks"], ensure_ascii=False),
            report["stats"]["total_articles"],
            stats.get("patent", 0),
            stats.get("policy", 0),
            report["impact"]["pro"],
            report["impact"]["scan"],
            report["impact"]["db"],
            json.dumps(report["rd_suggestions"], ensure_ascii=False),
        ))
        
        conn.commit()
        conn.close()
        
        print(f"\n[Orchestrator] ✓ 周报生成完成: {report_id}")
        print(f"[Orchestrator]   总情报数: {report['stats']['total_articles']}")
        print(f"[Orchestrator]   高价值文章: {len(top_articles)}")
        print(f"[Orchestrator]   政策倒计时: {len(policies)}")
        
        return report
    
    def _generate_judgment(self, articles, policies) -> str:
        """生成一句话判断"""
        critical_policies = [p for p in policies if p["impact_level"] == "critical"]
        
        if critical_policies:
            return f"本周{critical_policies[0]['title']}进入{ critical_policies[0]['days_left'] }天倒计时，CarbonSeek需加速CBAM合规模块开发；同时新增{len(articles)}条高价值情报，建议优先关注电池法规和碳标签互认进展。"
        else:
            return f"本周情报中心新增{len(articles)}条高价值情报，政策、学术、专利、行业四线并进，建议重点关注碳足迹核算标准建设和欧盟CBAM实施细则更新。"
    
    def _extract_key_changes(self, articles) -> List[Dict]:
        """提取重大变化"""
        return [
            {
                "rank": i+1,
                "title": a["title"],
                "source": a["source"],
                "severity": "critical" if a["relevance_score"] >= 0.8 else "high",
                "type": a["source_type"],
                "date": a["publish_date"],
            }
            for i, a in enumerate(articles[:5])
        ]
    
    def _extract_opportunities(self, articles) -> List[Dict]:
        """提取产品机会"""
        opportunities = []
        
        for article in articles:
            if article["relevance_score"] >= 0.6:
                opp = {
                    "title": article["title"],
                    "industry": article["industry"],
                    "score": article["relevance_score"],
                    "source_count": 1,
                    "status": "待评审"
                }
                opportunities.append(opp)
        
        return opportunities[:10]
    
    def _extract_risks(self, policies) -> List[Dict]:
        """提取风险预警"""
        return [
            {
                "policy": p["title"],
                "days_left": p["days_left"],
                "level": p["impact_level"],
                "action": p.get("carbseek_action", "密切关注")
            }
            for p in policies if p["days_left"] <= 90
        ]
    
    def _impact_on_pro(self, articles, policies) -> str:
        """分析对Pro产品的影响"""
        return "CBAM申报自动化和电池碳足迹声明模块需优先开发；碳标签互认功能待需求确认。"
    
    def _impact_on_scan(self, articles) -> str:
        """分析对Scan产品的影响"""
        return "需更新扫描识别规则库，增加韩国碳标签、欧盟电池法规相关标识的识别能力。"
    
    def _impact_on_db(self, articles) -> str:
        """分析对数据库的影响"""
        return "需补充化工行业上游排放因子、欧盟官方默认排放因子、韩国碳标签认证机构名录。"
    
    def _generate_rd_suggestions(self, articles, policies) -> List[str]:
        """生成研发建议"""
        return [
            "【P0】启动CBAM Q3申报模块开发，对接欧盟官方API",
            "【P0】完成电池碳足迹核算工具原型，支持LCA四个阶段",
            "【P1】扩展化工行业因子库，覆盖乙烯、甲醇等基础产品",
            "【P1】开发韩国碳标签对接模块，预研互认机制",
            "【P2】建设碳数据质量评分模型，提升数据可信度",
        ]
    
    def run_pipeline(self):
        """执行完整情报流水线"""
        # 1. 采集
        results = self.run_all_agents()
        
        # 2. 生成周报
        report = self.generate_weekly_report()
        
        # 3. 输出摘要
        print(f"\n{'='*60}")
        print(f"[Orchestrator] 情报流水线完成")
        print(f"{'='*60}")
        print(f"\n一句话判断:")
        print(f"  {report['one_sentence_judgment']}")
        print(f"\n统计:")
        for source, count in report["stats"]["by_source"].items():
            print(f"  - {source}: {count} 条")
        
        return report


if __name__ == "__main__":
    orch = Orchestrator()
    report = orch.run_pipeline()
    
    # 保存JSON
    output_path = Path(__file__).parent / "web" / "data" / "weekly_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n[Orchestrator] 周报已保存: {output_path}")
