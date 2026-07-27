#!/usr/bin/env python3
"""
Patent-Agent - 专利情报采集
===========================
IPC分类：G06Q50/26(环境经济), G01N(检测)
关键词：carbon footprint/label/tracking
"""
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent, IntelligenceItem


class PatentAgent(BaseAgent):
    """专利情报采集Agent"""
    
    def __init__(self):
        super().__init__("Patent-Agent", "patent")
        
        self.mock_patents = [
            {
                "title": "一种产品碳足迹自动化核算方法及系统",
                "abstract": "本发明公开了一种产品碳足迹自动化核算方法，包括：获取产品BOM清单；自动匹配排放因子数据库；计算各阶段碳排放量；生成碳足迹报告。解决了现有技术中碳足迹核算效率低、易出错的技术问题。",
                "applicant": "碳阻迹（北京）科技有限公司",
                "inventor": "李鹏, 王芳",
                "ipc": "G06Q50/26",
                "patent_type": "invention",
                "application_date": "2025-03-15",
                "publication_date": "2026-06-20",
                "legal_status": "granted",
                "carbseek_value": "high",
                "url": "https://www.incopat.com/"
            },
            {
                "title": "基于区块链的碳标签溯源系统",
                "abstract": "本发明涉及一种基于区块链技术的碳标签溯源系统，通过分布式账本记录产品全生命周期碳排放数据，确保碳标签数据不可篡改、可追溯。",
                "applicant": "阿里巴巴（中国）有限公司",
                "inventor": "张伟, 陈明",
                "ipc": "G06Q50/26",
                "patent_type": "invention",
                "application_date": "2024-11-08",
                "publication_date": "2026-05-12",
                "legal_status": "pending",
                "carbseek_value": "high",
                "url": "https://www.incopat.com/"
            },
            {
                "title": "碳排放检测设备及其数据处理装置",
                "abstract": "一种用于工业过程碳排放实时检测的装置，包括气体采样模块、光谱分析模块和数据处理单元，可实现CO2、CH4、N2O等温室气体的在线监测。",
                "applicant": "聚光科技（杭州）股份有限公司",
                "inventor": "刘洋, 赵敏",
                "ipc": "G01N21/3504",
                "patent_type": "utility",
                "application_date": "2025-06-22",
                "publication_date": "2026-01-10",
                "legal_status": "granted",
                "carbseek_value": "medium",
                "url": "https://www.incopat.com/"
            },
            {
                "title": "电池产品碳足迹计算模型及生命周期评价方法",
                "abstract": "本发明提出了一种适用于动力电池产品的碳足迹计算模型，综合考虑原材料获取、电芯制造、模组装配、Pack集成和回收处理五个阶段的碳排放。",
                "applicant": "宁德时代新能源科技股份有限公司",
                "inventor": "林涛, 黄丽",
                "ipc": "G06Q50/26",
                "patent_type": "invention",
                "application_date": "2025-01-18",
                "publication_date": "2026-04-15",
                "legal_status": "granted",
                "carbseek_value": "high",
                "url": "https://www.incopat.com/"
            },
            {
                "title": "供应链碳数据共享方法及装置",
                "abstract": "本申请提供了一种供应链碳数据共享方法，通过建立供应链上下游企业间的碳数据交换协议，实现范围三排放数据的自动化采集和验证。",
                "applicant": "华为技术有限公司",
                "inventor": "李强, 周芳",
                "ipc": "G06Q50/28",
                "patent_type": "invention",
                "application_date": "2025-09-05",
                "publication_date": "2026-07-01",
                "legal_status": "pending",
                "carbseek_value": "high",
                "url": "https://www.incopat.com/"
            },
            {
                "title": "一种化工产品碳足迹核算方法",
                "abstract": "针对化工行业多联产、副产品分摊等复杂场景，提出基于质量平衡和能量平衡的碳足迹核算方法，适用于乙烯、甲醇等基础化工产品。",
                "applicant": "中国石化集团",
                "inventor": "孙伟, 郑刚",
                "ipc": "G06Q50/26",
                "patent_type": "invention",
                "application_date": "2024-08-20",
                "publication_date": "2026-03-10",
                "legal_status": "granted",
                "carbseek_value": "medium",
                "url": "https://www.incopat.com/"
            },
        ]
    
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        items = []
        
        for patent in self.mock_patents:
            content = (patent["title"] + " " + patent["abstract"]).lower()
            matched = any(kw.lower() in content for kw in keywords)
            
            if matched or random.random() > 0.3:
                item = IntelligenceItem(
                    title=patent["title"],
                    summary=patent["abstract"],
                    url=patent["url"],
                    source="incopat",
                    source_type="patent",
                    publish_date=patent["publication_date"],
                    author=patent["inventor"],
                    keywords=json.dumps(["专利", patent["ipc"]], ensure_ascii=False),
                    raw_data=json.dumps(patent, ensure_ascii=False)
                )
                items.append(item)
        
        random.shuffle(items)
        return items[:5]
    
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        return IntelligenceItem(
            title=raw_data.get("title", ""),
            summary=raw_data.get("abstract", ""),
            url=raw_data.get("url", ""),
            source="专利数据库",
            source_type="patent",
            publish_date=raw_data.get("publication_date", ""),
            raw_data=json.dumps(raw_data, ensure_ascii=False)
        )


if __name__ == "__main__":
    agent = PatentAgent()
    result = agent.run([
        "carbon footprint", "carbon label", "碳足迹",
        "碳标签", "碳核算", "LCA"
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
