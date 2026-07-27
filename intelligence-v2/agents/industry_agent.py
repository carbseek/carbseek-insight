#!/usr/bin/env python3
"""
Industry-Agent - 行业动态采集
==============================
行业协会、头部企业官网、展会信息
"""
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent, IntelligenceItem


class IndustryAgent(BaseAgent):
    """行业动态采集Agent"""
    
    def __init__(self):
        super().__init__("Industry-Agent", "industry")
        
        self.mock_projects = [
            {
                "title": "美的集团获家电行业首张产品碳足迹标识认证",
                "summary": "美的空调产品通过中国质量认证中心（CQC）碳足迹认证，成为家电行业首家获得产品碳足迹标识的企业。认证覆盖原材料获取、生产制造、运输分销和产品使用四个阶段。",
                "company": "美的集团",
                "industry": "电子电气",
                "project_type": "certification",
                "days_ago": 3,
                "url": "https://www.midea.com/news/"
            },
            {
                "title": "万华化学发布化工行业碳足迹管理平台2.0",
                "summary": "平台新增MDI、TDI等12种聚氨酯产品的碳足迹核算模块，实现从原材料采购到终端产品的全链条碳数据追踪。",
                "company": "万华化学",
                "industry": "化工",
                "project_type": "platform",
                "days_ago": 7,
                "url": "https://www.whchem.com/news/"
            },
            {
                "title": "比亚迪与SGS合作开展动力电池碳足迹核算",
                "summary": "比亚迪与SGS通标标准技术服务有限公司签署合作协议，对其刀片电池产品开展全生命周期碳足迹核算，以应对欧盟电池法规要求。",
                "company": "比亚迪",
                "industry": "汽车",
                "project_type": "partnership",
                "days_ago": 10,
                "url": "https://www.byd.com/news/"
            },
            {
                "title": "海尔智家启动欧盟出口产品CBAM合规项目",
                "summary": "海尔智家针对冰箱、洗衣机等出口欧盟的家电产品启动CBAM合规项目，建立产品碳足迹核算体系和供应商碳数据收集机制。",
                "company": "海尔智家",
                "industry": "欧盟出口",
                "project_type": "certification",
                "days_ago": 14,
                "url": "https://www.haier.com/news/"
            },
            {
                "title": "中化国际发布2026年可持续发展报告：化工产品碳足迹降低12%",
                "summary": "报告显示，中化国际主要化工产品碳足迹较2023年基准降低12%，完成首批5种产品的碳标签认证。",
                "company": "中化国际",
                "industry": "化工",
                "project_type": "certification",
                "days_ago": 18,
                "url": "https://www.sinochem.com/news/"
            },
            {
                "title": "TCL电子加入产品碳足迹数字化试点项目",
                "summary": "TCL电子参与工信部产品碳足迹数字化试点，通过数字化手段实现电视产品全生命周期碳数据的自动采集和分析。",
                "company": "TCL电子",
                "industry": "电子电气",
                "project_type": "pilot",
                "days_ago": 21,
                "url": "https://www.tcl.com/news/"
            },
            {
                "title": "第18届中国国际低碳产业博览会将于8月举办",
                "summary": "展会聚焦碳足迹核算、碳标签认证、碳数据平台等主题，预计将吸引500余家国内外企业参展。",
                "company": "中国低碳经济发展促进会",
                "industry": "通用",
                "project_type": "platform",
                "days_ago": 25,
                "url": "https://www.ccepa.org.cn/"
            },
        ]
    
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        items = []
        
        for project in self.mock_projects:
            content = (project["title"] + " " + project["summary"]).lower()
            matched = any(kw.lower() in content for kw in keywords)
            
            if matched or random.random() > 0.3:
                item = IntelligenceItem(
                    title=project["title"],
                    summary=project["summary"],
                    url=project["url"],
                    source=project["company"],
                    source_type="industry",
                    publish_date=(datetime.now() - timedelta(days=project["days_ago"])).strftime("%Y-%m-%d"),
                    industry=project["industry"],
                    topic=project["project_type"],
                    raw_data=json.dumps(project, ensure_ascii=False)
                )
                items.append(item)
        
        random.shuffle(items)
        return items[:6]
    
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        return IntelligenceItem(
            title=raw_data.get("title", ""),
            summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            source=raw_data.get("company", "行业协会"),
            source_type="industry",
            publish_date=raw_data.get("date", ""),
            raw_data=json.dumps(raw_data, ensure_ascii=False)
        )


if __name__ == "__main__":
    agent = IndustryAgent()
    result = agent.run([
        "碳足迹", "碳标签", "CBAM", "认证",
        "碳核算", "欧盟", "电池"
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
