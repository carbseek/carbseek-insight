#!/usr/bin/env python3
"""
CarbSeek Intelligence - 数据库初始化
=====================================
"""
import sqlite3
import json
from pathlib import Path
from schema import SCHEMA_SQL, INITIAL_POLICIES

DB_PATH = Path(__file__).parent / "carbseek_intel.db"


def init_database():
    """初始化数据库"""
    print(f"[DB] 初始化数据库: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 执行Schema
    cursor.executescript(SCHEMA_SQL)
    
    # 插入初始政策数据
    for policy in INITIAL_POLICIES:
        cursor.execute("""
            INSERT OR IGNORE INTO policies 
            (policy_id, title, issuing_body, policy_type, region, 
             publish_date, effective_date, deadline_date, days_left,
             impact_level, affected_industries, carbseek_action, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            policy["policy_id"], policy["title"], policy["issuing_body"],
            policy["policy_type"], policy["region"],
            policy["publish_date"], policy["effective_date"],
            policy["deadline_date"], policy["days_left"],
            policy["impact_level"], policy["affected_industries"],
            policy["carbseek_action"], policy["url"]
        ))
    
    conn.commit()
    
    # 验证
    cursor.execute("SELECT COUNT(*) as count FROM policies")
    policy_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    
    conn.close()
    
    print(f"[DB] ✓ 数据库初始化完成")
    print(f"[DB]   - 表数量: {len(tables)}")
    print(f"[DB]   - 初始政策: {policy_count} 条")
    print(f"[DB]   - 表列表: {', '.join(tables)}")
    
    return DB_PATH


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_database()
