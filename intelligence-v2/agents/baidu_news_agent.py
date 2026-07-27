#!/usr/bin/env python3
"""
BaiduNews-Agent - 百度新闻与学术情报采集
=========================================
关键词：碳足迹、碳标签、碳标识、产品碳足迹、碳认证、CBAM、欧盟电池法规
"""
import sys
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_agent import BaseAgent, IntelligenceItem


class BaiduNewsAgent(BaseAgent):
    """百度新闻采集Agent - 模拟数据版本"""
    
    def __init__(self):
        super().__init__("BaiduNews-Agent", "news")
        
        # 模拟新闻数据源
        self.mock_news = [
            {
                "title": "生态环境部：产品碳足迹管理体系建设进展报告（2026）发布",
                "summary": "报告指出，截至2026年7月，全国已有20余个省市编制地方碳足迹管理方案，覆盖钢铁、化工、电子电气等重点行业。",
                "source": "生态环境部官网",
                "industry": "通用",
                "topic": "碳足迹",
                "days_ago": 2,
                "url": "https://www.mee.gov.cn/xxgk/xxgk/"
            },
            {
                "title": "欧盟CBAM Q3申报指南发布：新增12类铝制品追溯要求",
                "summary": "欧盟委员会发布第三季度CBAM申报指南，新增铝型材、铝箔等12类产品的上游排放追溯要求，中国企业需提前准备供应链碳数据。",
                "source": "European Commission TAXUD",
                "industry": "欧盟出口",
                "topic": "CBAM",
                "days_ago": 3,
                "url": "https://taxation-customs.ec.europa.eu/"
            },
            {
                "title": "宁德时代发布2026年碳中和进展报告：电池碳足迹降低18%",
                "summary": "宁德时代发布年度可持续发展报告，显示其动力电池产品碳足迹较2023年基准降低18%，并完成首个海外工厂碳中和认证。",
                "source": "宁德时代官网",
                "industry": "汽车",
                "topic": "碳足迹",
                "days_ago": 1,
                "url": "https://www.catl.com/news/"
            },
            {
                "title": "韩国K-碳标签制度7月更新：新增家电产品类别",
                "summary": "韩国产业通商资源部更新K-碳标签产品目录，新增空调、洗衣机等白色家电类别，2027年1月起强制实施。",
                "source": "韩国产业通商资源部",
                "industry": "电子电气",
                "topic": "碳标签",
                "days_ago": 5,
                "url": "https://www.motie.go.kr/"
            },
            {
                "title": "中国石化联合会发布化工行业碳足迹核算指南（试行）",
                "summary": "指南涵盖乙烯、甲醇、合成氨等12种基础化工产品的碳足迹核算方法，为企业提供标准化核算路径。",
                "source": "中国石化联合会",
                "industry": "化工",
                "topic": "碳足迹核算",
                "days_ago": 7,
                "url": "https://www.cpcia.org.cn/"
            },
            {
                "title": "欧盟电池法规碳足迹声明平台正式上线",
                "summary": "欧盟电池法规要求的碳足迹声明平台正式启用，电池制造商需通过平台提交产品碳足迹报告，首批涉及动力电池和储能电池。",
                "source": "EU Battery Observatory",
                "industry": "汽车",
                "topic": "欧盟电池法规",
                "days_ago": 4,
                "url": "https://batteries.ec.europa.eu/"
            },
            {
                "title": "清华大学研究团队：中国产品碳足迹因子库建设路径研究",
                "summary": "研究提出分阶段建设国家产品碳足迹因子库的建议，包括基础数据层、核算方法层和应用服务层三层架构。",
                "source": "百度学术",
                "industry": "通用",
                "topic": "LCA",
                "days_ago": 10,
                "url": "https://xueshu.baidu.com/"
            },
            {
                "title": "巴斯夫与SABIC签署化工行业Scope 3碳数据共享协议",
                "summary": "两家化工巨头将共享上游原材料的碳排放数据，推动化工行业供应链碳透明度，涉及1000余种基础化学品。",
                "source": "巴斯夫官网",
                "industry": "化工",
                "topic": "Scope 3",
                "days_ago": 6,
                "url": "https://www.basf.com/global/news/"
            },
            {
                "title": "中国机电商会：欧盟CBAM对机电产品出口影响评估报告",
                "summary": "报告测算，CBAM全面实施后，中国机电产品对欧出口成本将增加3-8%，建议企业加快碳足迹核算能力建设。",
                "source": "中国机电商会",
                "industry": "欧盟出口",
                "topic": "CBAM",
                "days_ago": 8,
                "url": "https://www.cccme.org.cn/"
            },
            {
                "title": "TÜV莱茵推出电子产品碳标签认证服务",
                "summary": "TÜV莱茵在中国市场推出电子产品碳标签认证，覆盖手机、笔记本电脑、显示器等消费电子产品。",
                "source": "TÜV莱茵",
                "industry": "电子电气",
                "topic": "碳标签",
                "days_ago": 9,
                "url": "https://www.tuv.com/news/"
            },
        ]
    
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        """模拟搜索 - 实际部署时接入百度搜索API"""
        items = []
        
        # 根据关键词筛选相关新闻
        for news in self.mock_news:
            title_summary = (news["title"] + " " + news["summary"]).lower()
            
            # 检查是否匹配任一关键词
            matched = any(kw.lower() in title_summary for kw in keywords)
            
            if matched or random.random() > 0.3:  # 随机添加一些，模拟实际搜索
                item = IntelligenceItem(
                    title=news["title"],
                    summary=news["summary"],
                    url=news["url"],
                    source=news["source"],
                    source_type="news",
                    publish_date=(datetime.now() - timedelta(days=news["days_ago"])).strftime("%Y-%m-%d"),
                    industry=news["industry"],
                    topic=news["topic"],
                    raw_data=json.dumps(news, ensure_ascii=False)
                )
                items.append(item)
        
        # 随机打乱，模拟不同时间搜索结果不同
        random.shuffle(items)
        return items[:8]  # 限制返回数量
    
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        """解析百度搜索结果"""
        return IntelligenceItem(
            title=raw_data.get("title", ""),
            summary=raw_data.get("summary", ""),
            url=raw_data.get("url", ""),
            source=raw_data.get("source", "百度"),
            source_type="news",
            publish_date=raw_data.get("date", ""),
            raw_data=json.dumps(raw_data, ensure_ascii=False)
        )


if __name__ == "__main__":
    agent = BaiduNewsAgent()
    result = agent.run([
        "碳足迹", "碳标签", "CBAM", "欧盟电池法规",
        "产品碳足迹", "碳认证", "LCA"
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
