#!/usr/bin/env python3
"""
CNKI-Agent - 学术情报采集
=========================
核心期刊论文、硕博论文、会议论文
关键词：生命周期评价(LCA)、碳足迹核算、碳标签体系
"""
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent, IntelligenceItem


class CNKIAgent(BaseAgent):
    """学术情报采集Agent"""
    
    def __init__(self):
        super().__init__("CNKI-Agent", "academic")
        
        self.mock_papers = [
            {
                "title": "基于LCA的锂电池全生命周期碳足迹核算方法研究",
                "summary": "构建了涵盖原材料获取、电池制造、使用阶段和回收处理四个阶段的生命周期评价模型，量化分析磷酸铁锂电池的碳足迹分布特征。",
                "author": "张明华, 李强, 王晓东",
                "source": "环境科学学报",
                "industry": "汽车",
                "topic": "LCA",
                "days_ago": 12,
                "doi": "10.13227/j.hjkx.2026xxxx",
                "url": "https://www.cnki.net/"
            },
            {
                "title": "欧盟CBAM机制下中国出口产品碳足迹核算边界研究",
                "summary": "对比分析了CBAM默认排放因子与中国本土化因子的差异，提出面向欧盟出口企业的碳足迹核算边界优化方案。",
                "author": "陈思远, 刘洋",
                "source": "国际贸易问题",
                "industry": "欧盟出口",
                "topic": "CBAM",
                "days_ago": 18,
                "doi": "10.13510/j.cnki.jit.2026xxxx",
                "url": "https://www.cnki.net/"
            },
            {
                "title": "化工行业产品碳标签体系构建与实证分析",
                "summary": "以聚乙烯产品为例，构建了包含原料碳足迹、生产过程碳足迹和运输碳足迹三层次的产品碳标签体系。",
                "author": "赵敏, 孙伟",
                "source": "化工进展",
                "industry": "化工",
                "topic": "碳标签",
                "days_ago": 8,
                "doi": "10.16085/j.issn.1000-6613.2026xxxx",
                "url": "https://www.cnki.net/"
            },
            {
                "title": "电气电子产品碳足迹核算中范围三排放的分配方法比较",
                "summary": "对比分析了经济分配、物理分配和混合分配三种方法在电气电子产品上游排放分配中的适用性。",
                "author": "周芳, 吴磊",
                "source": "中国电机工程学报",
                "industry": "电子电气",
                "topic": "Scope 3",
                "days_ago": 15,
                "doi": "10.13334/j.0258-8013.pcsee.2026xxxx",
                "url": "https://www.cnki.net/"
            },
            {
                "title": "产品碳足迹核算标准PCR开发方法论研究——以家电产品为例",
                "summary": "系统梳理了ISO 14025和EPD体系下PCR的开发流程，提出面向中国家电行业的PCR编制指南。",
                "author": "黄丽, 郑刚",
                "source": "标准科学",
                "industry": "电子电气",
                "topic": "PCR",
                "days_ago": 20,
                "doi": "10.3969/j.issn.1674-5698.2026xxxx",
                "url": "https://www.cnki.net/"
            },
            {
                "title": "碳足迹大数据平台建设中的数据质量控制框架设计",
                "summary": "提出基于区块链技术的碳足迹数据溯源机制，解决数据可信度验证和供应链碳数据共享问题。",
                "author": "林涛, 何静",
                "source": "大数据",
                "industry": "通用",
                "topic": "碳数据平台",
                "days_ago": 25,
                "doi": "10.11959/j.issn.2096-0271.2026xxxx",
                "url": "https://www.cnki.net/"
            },
        ]
    
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        """模拟学术搜索"""
        items = []
        
        for paper in self.mock_papers:
            content = (paper["title"] + " " + paper["summary"]).lower()
            matched = any(kw.lower() in content for kw in keywords)
            
            if matched or random.random() > 0.4:
                item = IntelligenceItem(
                    title=paper["title"],
                    summary=paper["summary"],
                    url=paper["url"],
                    source=paper["source"],
                    source_type="academic",
                    publish_date=(datetime.now() - timedelta(days=paper["days_ago"])).strftime("%Y-%m-%d"),
                    industry=paper["industry"],
                    topic=paper["topic"],
                    author=paper["author"],
                    keywords=json.dumps(["LCA", "碳足迹", paper["topic"]], ensure_ascii=False),
                    raw_data=json.dumps(paper, ensure_ascii=False)
                )
                items.append(item)
        
        random.shuffle(items)
        return items[:6]
    
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        return IntelligenceItem(
            title=raw_data.get("title", ""),
            summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            source=raw_data.get("source", "CNKI"),
            source_type="academic",
            publish_date=raw_data.get("date", ""),
            author=raw_data.get("author", ""),
            raw_data=json.dumps(raw_data, ensure_ascii=False)
        )


if __name__ == "__main__":
    agent = CNKIAgent()
    result = agent.run([
        "生命周期评价", "LCA", "碳足迹核算", "碳标签体系",
        "Scope 3", "PCR", "EPD"
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
