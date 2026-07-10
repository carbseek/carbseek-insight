#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CarbSeek Insight - 情报采集与周报生成引擎
============================================

功能：
1. 每周自动追踪全球碳产业动态（政策、学术、专利、竞品、行业应用）
2. 生成 HTML 情报驾驶舱
3. 更新机会库、证据库、行业趋势数据

执行方式：
    python insight_engine.py --week 2026-W29

依赖：
    - Python 3.9+
    - 可选：kimi_search_v2, kimi_fetch_v2 等数据工具（实际部署时接入）

作者：CarbSeek Insight Agent
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================
# 数据模型定义
# ============================================================

class EvidenceType(str, Enum):
    POLICY = "政策"
    ACADEMIC = "学术"
    PATENT = "专利"
    COMPETITOR = "竞品"
    INDUSTRY = "行业应用"
    NEWS = "新闻"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class OpportunityStatus(str, Enum):
    PENDING = "待评审"
    APPROVED = "已立项"
    LAUNCHED = "已上线"
    ARCHIVED = "已归档"

class RevenuePotential(str, Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

@dataclass
class Evidence:
    evidence_id: str
    title: str
    source: str
    source_url: str
    date: str
    industry: str
    theme: str
    abstract: str
    key_evidence: str
    agent_explanation: str
    credibility: str  # 高/中/低
    in_product_pool: bool
    opportunity_ids: List[str]
    evidence_type: str

@dataclass
class RadarItem:
    radar_id: str
    title: str
    category: str  # 政策变化/学术前沿/专利动态/竞品动作/行业应用/风险预警
    severity: str
    industry: str
    date: str
    summary: str
    evidence_ids: List[str]
    action_required: bool

@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    industry: str
    theme: str
    source_count: int
    evidence_grade: str
    business_value: int
    tech_feasibility: int
    revenue_potential: str
    suggested_owner: str
    status: str
    created_at: str
    updated_at: str
    evidence_ids: List[str]
    description: str
    impact_pro: str
    impact_scan: str
    impact_db: str

@dataclass
class WeeklyReport:
    report_id: str
    week_ending: str
    one_sentence_judgment: str
    policy_changes: List[RadarItem]
    academic_frontier: List[RadarItem]
    patent_dynamics: List[RadarItem]
    competitor_dynamics: List[RadarItem]
    industry_applications: Dict[str, List[RadarItem]]
    impact_pro: str
    impact_scan: str
    impact_db: str
    top_opportunities: List[Opportunity]
    rd_suggestions: List[str]
    appendix: List[Evidence]


# ============================================================
# 配置常量
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PAGES_DIR = BASE_DIR / "pages"

# 追踪关键词配置
TRACKING_CONFIG = {
    "industries": ["化工", "电子电气", "汽车", "欧盟出口型行业"],
    "themes": ["碳足迹", "碳标签", "LCA", "CBAM", "EPD", "PCR", "Scope 3", "碳核算", "碳数据平台"],
    "sources": {
        "policy": [
            "欧盟官方公报 (EU Official Journal)",
            "European Commission - TAXUD",
            "ISO 标准更新",
            "中国各部委政策文件",
            "韩国产业通商资源部"
        ],
        "academic": [
            "Nature Communications",
            "Science",
            "Environmental Science & Technology",
            "Journal of Cleaner Production",
            "Transportation Research Part D"
        ],
        "patent": [
            "USPTO",
            "EPO",
            "CNIPA (中国专利局)",
            "WIPO"
        ],
        "competitor": [
            "碳阻迹",
            "妙盈科技",
            "远景碳管理",
            "TÜV/SGS/Intertek",
            "MSCI/Sustainalytics",
            "各大企业年报/ESG报告"
        ]
    }
}


# ============================================================
# 采集器接口（框架层，实际部署时接入真实数据源）
# ============================================================

class BaseCollector:
    """采集器基类"""
    name = "base"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        """采集指定周的数据，返回证据列表"""
        raise NotImplementedError

class SimulatedCollector(BaseCollector):
    """模拟采集器：用于测试和演示"""
    name = "simulated"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        """返回模拟数据（实际部署时替换为真实采集逻辑）"""
        # 这里可以接入 kimi_search_v2、kimi_fetch_v2 等工具
        # 示例：
        # results = kimi_search_v2(query="CBAM 2026 new policy")
        # for result in results:
        #     evidence = Evidence(...)
        #     evidences.append(evidence)
        return []

class PolicyCollector(BaseCollector):
    """政策采集器"""
    name = "policy"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        # TODO: 接入欧盟官方 API、中国政策数据库等
        # 示例搜索关键词：
        keywords = ["CBAM", "EU Battery Regulation", "carbon footprint regulation", "碳足迹 政策"]
        return []

class AcademicCollector(BaseCollector):
    """学术采集器"""
    name = "academic"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        # TODO: 接入 arXiv、Google Scholar、PubMed 等
        keywords = [
            "life cycle assessment carbon footprint",
            "Scope 3 emissions methodology",
            "product carbon footprint uncertainty"
        ]
        return []

class PatentCollector(BaseCollector):
    """专利采集器"""
    name = "patent"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        # TODO: 接入 Google Patents、专利局 API 等
        keywords = [
            "carbon footprint calculation",
            "LCA database",
            "carbon label verification"
        ]
        return []

class CompetitorCollector(BaseCollector):
    """竞品采集器"""
    name = "competitor"
    
    def collect(self, week_start: str, week_end: str) -> List[Evidence]:
        # TODO: 接入企业官网、新闻源、融资数据库等
        keywords = [
            "碳阻迹 融资",
            "妙盈科技 产品发布",
            "碳管理软件 新功能"
        ]
        return []


# ============================================================
# 情报处理引擎
# ============================================================

class IntelligenceEngine:
    """情报处理引擎：去重、评分、分类、关联"""
    
    def __init__(self):
        self.collectors: List[BaseCollector] = [
            PolicyCollector(),
            AcademicCollector(),
            PatentCollector(),
            CompetitorCollector(),
        ]
    
    def run_collection(self, week_start: str, week_end: str) -> List[Evidence]:
        """执行采集流程"""
        all_evidence = []
        for collector in self.collectors:
            print(f"[采集] 使用 {collector.name} 采集器...")
            evidence_list = collector.collect(week_start, week_end)
            all_evidence.extend(evidence_list)
            print(f"[采集] {collector.name} 采集到 {len(evidence_list)} 条证据")
        
        # 去重（基于标题相似度）
        all_evidence = self._deduplicate(all_evidence)
        print(f"[处理] 去重后剩余 {len(all_evidence)} 条证据")
        
        return all_evidence
    
    def _deduplicate(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """基于标题相似度去重"""
        seen_titles = set()
        unique = []
        for ev in evidence_list:
            # 简化去重：完全匹配标题
            if ev.title not in seen_titles:
                seen_titles.add(ev.title)
                unique.append(ev)
        return unique
    
    def score_evidence(self, evidence: Evidence) -> float:
        """为证据打分（0-100）"""
        score = 0
        # 来源可信度
        credibility_scores = {"高": 30, "中": 20, "低": 10}
        score += credibility_scores.get(evidence.credibility, 0)
        
        # 类型权重
        type_weights = {
            "政策": 25, "学术": 20, "专利": 15,
            "竞品": 20, "行业应用": 15, "新闻": 5
        }
        score += type_weights.get(evidence.evidence_type, 0)
        
        # 是否关联机会
        if evidence.opportunity_ids:
            score += 15
        
        # 是否已进入产品池
        if evidence.in_product_pool:
            score += 10
        
        return min(score, 100)
    
    def generate_radar_items(self, evidence_list: List[Evidence]) -> List[RadarItem]:
        """从证据生成雷达项"""
        radar_items = []
        for i, ev in enumerate(evidence_list):
            # 根据证据类型映射到雷达类别
            category_map = {
                "政策": "政策变化",
                "学术": "学术前沿",
                "专利": "专利动态",
                "竞品": "竞品动作",
                "行业应用": "行业应用",
                "新闻": "行业应用"
            }
            
            # 根据分数确定严重程度
            score = self.score_evidence(ev)
            if score >= 80:
                severity = Severity.CRITICAL
            elif score >= 60:
                severity = Severity.HIGH
            elif score >= 40:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            radar = RadarItem(
                radar_id=f"RD-{ev.date.replace('-', '')}-{i+1:02d}",
                title=ev.title,
                category=category_map.get(ev.evidence_type, "行业应用"),
                severity=severity.value,
                industry=ev.industry,
                date=ev.date,
                summary=ev.abstract[:100] + "..." if len(ev.abstract) > 100 else ev.abstract,
                evidence_ids=[ev.evidence_id],
                action_required=severity in (Severity.CRITICAL, Severity.HIGH)
            )
            radar_items.append(radar)
        
        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        radar_items.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return radar_items


# ============================================================
# 报告生成器
# ============================================================

class ReportGenerator:
    """HTML 报告生成器"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or BASE_DIR
    
    def generate_weekly_report(self, report: WeeklyReport, output_path: Path):
        """生成周报 HTML"""
        # 这里简化处理，实际应使用 Jinja2 等模板引擎
        # 当前版本复用已有的 index.html 结构
        
        html = self._render_report_html(report)
        output_path.write_text(html, encoding="utf-8")
        print(f"[报告] 已生成周报: {output_path}")
    
    def _render_report_html(self, report: WeeklyReport) -> str:
        """渲染报告 HTML（简化版，实际应使用模板）"""
        # 由于模板较长，这里提供一个简化框架
        # 实际使用时，可以基于已有的 index.html 做模板替换
        
        # 读取现有模板
        template_path = BASE_DIR / "index.html"
        if template_path.exists():
            html = template_path.read_text(encoding="utf-8")
            # TODO: 替换模板中的动态内容
            # html = html.replace("{{week_ending}}", report.week_ending)
            # html = html.replace("{{judgment}}", report.one_sentence_judgment)
            return html
        
        return "<!-- 模板未找到 -->"
    
    def update_data_files(self, evidence_list: List[Evidence], 
                          opportunities: List[Opportunity],
                          radar_items: List[RadarItem],
                          report_meta: Dict[str, Any]):
        """更新 JSON 数据文件"""
        # 更新证据库
        evidence_path = DATA_DIR / "evidence" / "evidence_pool.json"
        if evidence_path.exists():
            with open(evidence_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        
        # 合并新旧证据（去重）
        existing_ids = {e["evidence_id"] for e in existing}
        for ev in evidence_list:
            if ev.evidence_id not in existing_ids:
                existing.append(asdict(ev))
        
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        # 更新本周雷达
        radar_path = DATA_DIR / "radar" / "this_week.json"
        with open(radar_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in radar_items], f, ensure_ascii=False, indent=2)
        
        # 更新机会库
        opp_path = DATA_DIR / "opportunities" / "opportunity_pool.json"
        with open(opp_path, "w", encoding="utf-8") as f:
            json.dump([asdict(o) for o in opportunities], f, ensure_ascii=False, indent=2)
        
        # 更新周报元数据
        report_path = DATA_DIR / "reports" / f"{report_meta['report_id']}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_meta, f, ensure_ascii=False, indent=2)
        
        print(f"[数据] 已更新所有数据文件")


# ============================================================
# 主执行流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="CarbSeek Insight 情报引擎")
    parser.add_argument("--week", type=str, help="目标周，格式：YYYY-WNN")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入文件")
    parser.add_argument("--collect-only", action="store_true", help="仅执行采集")
    parser.add_argument("--generate-only", action="store_true", help="仅生成报告")
    args = parser.parse_args()
    
    # 确定目标周
    if args.week:
        target_week = args.week
    else:
        today = datetime.now()
        target_week = today.strftime("%Y-W%W")
    
    print(f"=" * 60)
    print(f"CarbSeek Insight 情报引擎")
    print(f"目标周: {target_week}")
    print(f"=" * 60)
    
    # 初始化引擎
    engine = IntelligenceEngine()
    generator = ReportGenerator()
    
    # 计算周起止日期
    week_num = int(target_week.split("-W")[1])
    year = int(target_week.split("-W")[0])
    week_start = datetime.strptime(f"{year}-W{week_num-1}-1", "%Y-W%W-%w").strftime("%Y-%m-%d")
    week_end = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
    
    print(f"[时间] {week_start} ~ {week_end}")
    
    if not args.generate_only:
        # 执行采集
        print("\n[阶段 1/3] 情报采集")
        evidence_list = engine.run_collection(week_start, week_end)
        
        if args.collect_only:
            print(f"\n[完成] 采集到 {len(evidence_list)} 条证据")
            return
    else:
        # 从现有数据加载
        evidence_list = []
    
    if not args.collect_only:
        # 生成雷达项
        print("\n[阶段 2/3] 情报处理")
        radar_items = engine.generate_radar_items(evidence_list)
        
        # 加载现有机会
        opp_path = DATA_DIR / "opportunities" / "opportunity_pool.json"
        if opp_path.exists():
            with open(opp_path, "r", encoding="utf-8") as f:
                opp_data = json.load(f)
            opportunities = [Opportunity(**o) for o in opp_data]
        else:
            opportunities = []
        
        # 构建周报元数据
        report_meta = {
            "report_id": f"WR-{target_week}",
            "week_ending": week_end,
            "one_sentence_judgment": "（请根据实际情况填写本周一句话判断）",
            "impact_pro": "（请填写对 Pro 的影响）",
            "impact_scan": "（请填写对 Scan 的影响）",
            "impact_db": "（请填写对数据库的影响）",
            "rd_suggestions": []
        }
        
        # 更新数据文件
        if not args.dry_run:
            print("\n[阶段 3/3] 数据持久化")
            generator.update_data_files(evidence_list, opportunities, radar_items, report_meta)
        else:
            print("\n[试运行] 跳过数据写入")
        
        print(f"\n[完成] CarbSeek Insight {target_week} 情报处理完成")
        print(f"  - 新增证据: {len(evidence_list)} 条")
        print(f"  - 雷达项: {len(radar_items)} 条")
        print(f"  - 产品机会: {len(opportunities)} 个")


if __name__ == "__main__":
    main()
