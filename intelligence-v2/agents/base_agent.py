#!/usr/bin/env python3
"""
CarbSeek Intelligence - Agent 基类框架
========================================
所有Sub-Agent的抽象基类
"""
import json
import hashlib
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 导入数据库连接
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from init_db import get_connection


@dataclass
class IntelligenceItem:
    """情报条目数据模型"""
    title: str
    summary: str = ""
    url: str = ""
    source: str = ""
    source_type: str = "news"  # news/academic/patent/policy/industry
    publish_date: str = ""
    industry: str = "通用"
    topic: str = ""
    author: str = ""
    keywords: str = "[]"  # JSON数组
    relevance_score: float = 0.0
    evidence_grade: str = "C"
    raw_data: str = "{}"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def generate_id(self) -> str:
        """生成唯一ID"""
        content = f"{self.title}{self.source}{self.publish_date}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ART-{timestamp}-{hash_val}"


class BaseAgent(ABC):
    """情报采集Agent基类"""
    
    def __init__(self, agent_name: str, source_type: str):
        self.agent_name = agent_name
        self.source_type = source_type
        self.items_collected = 0
        self.items_new = 0
        self.errors = []
        
    @abstractmethod
    def search(self, keywords: List[str], **kwargs) -> List[IntelligenceItem]:
        """执行搜索采集"""
        pass
    
    @abstractmethod
    def parse_result(self, raw_data: Dict) -> IntelligenceItem:
        """解析原始数据为结构化条目"""
        pass
    
    def calculate_relevance(self, item: IntelligenceItem) -> float:
        """计算相关度评分"""
        score = 0.0
        title_lower = item.title.lower()
        summary_lower = item.summary.lower()
        combined = title_lower + " " + summary_lower
        
        # 核心关键词匹配
        core_keywords = {
            "碳足迹": 0.30, "碳标签": 0.30, "碳标识": 0.30,
            "碳认证": 0.25, "产品碳足迹": 0.35,
            "lca": 0.25, "生命周期评价": 0.25,
            "cbam": 0.30, "碳边境": 0.30,
            "epd": 0.20, "pcr": 0.20,
            "scope 3": 0.25, "范围三": 0.25,
            "碳核算": 0.25, "碳数据": 0.20,
            "电池法规": 0.25, "欧盟电池": 0.25,
        }
        
        for keyword, weight in core_keywords.items():
            if keyword in combined:
                score += weight
        
        # 行业关键词
        industry_keywords = {
            "电气": 0.15, "电子": 0.15, "家电": 0.15,
            "化工": 0.15, "化学": 0.15, "塑料": 0.10,
            "汽车": 0.15, "电池": 0.15, "新能源": 0.10,
            "出口": 0.15, "外贸": 0.15, "欧盟": 0.15,
            "钢铁": 0.10, "水泥": 0.10, "铝": 0.10,
        }
        
        for keyword, weight in industry_keywords.items():
            if keyword in combined:
                score += weight
        
        # 来源加分
        high_quality_sources = ["gov.cn", "ec.europa", "nature", "ieee", 
                               "cnki", "wanfang", "epo", "wipo", "uspto"]
        if any(src in item.source.lower() for src in high_quality_sources):
            score += 0.15
        
        # 含具体数据加分
        if any(c.isdigit() for c in item.title):
            score += 0.10
        
        return min(score, 1.0)
    
    def deduplicate(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """去重：基于URL+标题MD5"""
        seen = set()
        unique_items = []
        
        for item in items:
            key = hashlib.md5(f"{item.title}{item.url}".encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items
    
    def save_to_database(self, items: List[IntelligenceItem]) -> int:
        """保存到数据库，返回新增数量"""
        conn = get_connection()
        cursor = conn.cursor()
        new_count = 0
        
        for item in items:
            article_id = item.generate_id()
            
            # 检查是否已存在（基于URL）
            cursor.execute("SELECT id FROM articles WHERE url = ?", (item.url,))
            if cursor.fetchone():
                continue
            
            # 计算相关度
            item.relevance_score = self.calculate_relevance(item)
            
            # 确定证据等级
            if item.relevance_score >= 0.7:
                item.evidence_grade = "A"
            elif item.relevance_score >= 0.5:
                item.evidence_grade = "B"
            elif item.relevance_score >= 0.3:
                item.evidence_grade = "C"
            else:
                item.evidence_grade = "D"
            
            cursor.execute("""
                INSERT INTO articles 
                (article_id, title, summary, url, source, source_type,
                 publish_date, industry, topic, author, keywords,
                 relevance_score, evidence_grade, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article_id, item.title, item.summary, item.url, 
                item.source, item.source_type, item.publish_date,
                item.industry, item.topic, item.author, item.keywords,
                item.relevance_score, item.evidence_grade, item.raw_data
            ))
            new_count += 1
        
        conn.commit()
        conn.close()
        
        self.items_new = new_count
        return new_count
    
    def log_run(self, status: str, duration: int):
        """记录Agent运行日志"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_runs 
            (agent_name, status, items_collected, items_new, error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.agent_name, status, self.items_collected, 
            self.items_new, ";".join(self.errors) if self.errors else None,
            duration
        ))
        
        conn.commit()
        conn.close()
    
    def run(self, keywords: List[str], **kwargs) -> Dict:
        """完整的Agent运行流程"""
        import time
        start_time = time.time()
        
        print(f"\n[{'='*50}")
        print(f"[Agent] {self.agent_name} 开始运行")
        print(f"[Agent] 关键词: {', '.join(keywords)}")
        print(f"[{'='*50}\n")
        
        try:
            # 1. 搜索采集
            items = self.search(keywords, **kwargs)
            self.items_collected = len(items)
            print(f"[Agent] 采集到 {len(items)} 条原始数据")
            
            # 2. 去重
            items = self.deduplicate(items)
            print(f"[Agent] 去重后剩余 {len(items)} 条")
            
            # 3. 保存到数据库
            new_count = self.save_to_database(items)
            print(f"[Agent] 新增入库 {new_count} 条")
            
            # 4. 记录运行日志
            duration = int(time.time() - start_time)
            status = "success" if new_count > 0 else "partial"
            self.log_run(status, duration)
            
            print(f"\n[Agent] ✓ {self.agent_name} 完成 ({duration}s)")
            
            return {
                "agent": self.agent_name,
                "status": status,
                "collected": self.items_collected,
                "new": new_count,
                "duration": duration,
                "errors": self.errors
            }
            
        except Exception as e:
            duration = int(time.time() - start_time)
            self.errors.append(str(e))
            self.log_run("failed", duration)
            
            print(f"\n[Agent] ✗ {self.agent_name} 失败: {str(e)}")
            
            return {
                "agent": self.agent_name,
                "status": "failed",
                "collected": 0,
                "new": 0,
                "duration": duration,
                "errors": self.errors
            }
