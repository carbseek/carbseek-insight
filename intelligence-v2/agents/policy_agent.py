#!/usr/bin/env python3
"""
Policy-Agent - 政策情报采集
===========================
市场监管总局、生态环境部、发改委、欧盟官网
"""
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent, IntelligenceItem


class PolicyAgent(BaseAgent):
    """政策情报采集Agent"""
    
    def __init__(self):
        super().__init__("Policy-Agent", "policy")
        
        self.mock_policies = [
            {
                "title": "生态环境部印发《2026年碳足迹管理重点工作清单》",
                "summary": "清单明确2026年下半年碳足迹管理五项重点工作：推进重点产品碳足迹核算、建设国家碳足迹因子数据库、完善碳标识认证制度、推动碳足迹国际互认、加强碳足迹数据质量监管。",
                "issuing_body": "生态环境部",
                "region": "中国",
                "impact_level": "critical",
                "days_ago": 5,
                "url": "https://www.mee.gov.cn/xxgk/"
            },
            {
                "title": "欧盟委员会发布CBAM Q3过渡期实施细则修订版",
                "summary": "修订版明确过渡期申报的碳排放核算边界、默认排放因子适用条件和实际排放数据替代规则，首次引入机加工排除条款和50吨微量豁免门槛。",
                "issuing_body": "European Commission",
                "region": "欧盟",
                "impact_level": "critical",
                "days_ago": 8,
                "url": "https://taxation-customs.ec.europa.eu/"
            },
            {
                "title": "市场监管总局发布《产品碳标识认证管理办法（征求意见稿）》",
                "summary": "办法拟建立统一的产品碳标识认证制度，明确认证机构资质、认证程序、标识使用规则和监督管理要求。公众意见反馈截止日期为2026年8月15日。",
                "issuing_body": "市场监管总局",
                "region": "中国",
                "impact_level": "high",
                "days_ago": 12,
                "url": "https://www.samr.gov.cn/"
            },
            {
                "title": "韩国修订《低碳产品认证制度施行细则》",
                "summary": "修订案扩大低碳产品认证范围，将半导体制造设备、LED照明产品纳入认证目录，并简化中小企业认证程序。",
                "issuing_body": "韩国环境部",
                "region": "韩国",
                "impact_level": "high",
                "days_ago": 15,
                "url": "https://www.me.go.kr/"
            },
            {
                "title": "国家发改委：将产品碳足迹纳入绿色工厂评价指标",
                "summary": "新版《绿色工厂评价通则》将产品碳足迹核算和碳标签认证作为绿色工厂评价的重要指标，推动制造业绿色低碳转型。",
                "issuing_body": "国家发改委",
                "region": "中国",
                "impact_level": "high",
                "days_ago": 20,
                "url": "https://www.ndrc.gov.cn/"
            },
            {
                "title": "美国EPA发布产品碳足迹核算指南草案",
                "summary": "指南草案借鉴ISO 14067和欧盟PEF框架，提出面向美国市场的产品碳足迹核算方法，重点覆盖消费品和电子产品。",
                "issuing_body": "US EPA",
                "region": "美国",
                "impact_level": "medium",
                "days_ago": 25,
                "url": "https://www.epa.gov/"
            },
        ]
    
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        items = []
        
        for policy in self.mock_policies:
            content = (policy["title"] + " " + policy["summary"]).lower()
            matched = any(kw.lower() in content for kw in keywords)
            
            if matched or random.random() > 0.3:
                item = IntelligenceItem(
                    title=policy["title"],
                    summary=policy["summary"],
                    url=policy["url"],
                    source=policy["issuing_body"],
                    source_type="policy",
                    publish_date=(datetime.now() - timedelta(days=policy["days_ago"])).strftime("%Y-%m-%d"),
                    industry="通用",
                    topic="政策",
                    raw_data=json.dumps(policy, ensure_ascii=False)
                )
                items.append(item)
        
        random.shuffle(items)
        return items[:6]
    
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        return IntelligenceItem(
            title=raw_data.get("title", ""),
            summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            source=raw_data.get("issuing_body", "政府部门"),
            source_type="policy",
            publish_date=raw_data.get("date", ""),
            raw_data=json.dumps(raw_data, ensure_ascii=False)
        )


if __name__ == "__main__":
    agent = PolicyAgent()
    result = agent.run([
        "碳足迹", "碳标签", "CBAM", "政策",
        "认证", "欧盟", "生态环境部"
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
