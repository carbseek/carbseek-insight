#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CarbSeek Insight 自动更新脚本
=============================
每周自动执行，更新情报驾驶舱的日期和倒计时

用法:
    python scripts/auto_update.py

功能:
    1. 更新 index.html 中的周报日期和倒计时天数
    2. 更新 data/policy_countdown.json
    3. 记录更新日志
"""

import json
import re
from datetime import datetime, date
from pathlib import Path

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path(__file__).parent.parent
HTML_FILE = BASE_DIR / "index.html"
POLICY_FILE = BASE_DIR / "data" / "policy_countdown.json"
LOG_FILE = BASE_DIR / "auto_update.log"

# 政策倒计时配置 (截止日期)
POLICIES = [
    {"name": "CBAM 正式征收（取消免费配额）", "deadline": date(2026, 10, 1), "urgency": "critical"},
    {"name": "韩国电子电气碳标签过渡期结束", "deadline": date(2026, 12, 31), "urgency": "high"},
    {"name": "欧盟电池法规碳足迹强制声明", "deadline": date(2027, 2, 18), "urgency": "critical"},
    {"name": "CBAM 扩大至有机化学品、塑料", "deadline": date(2027, 1, 1), "urgency": "high"},
]


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def calculate_days_left(deadline: date) -> int:
    """计算距离截止日期的剩余天数"""
    today = date.today()
    delta = deadline - today
    return max(delta.days, 0)


def get_week_info() -> tuple:
    """获取当前周信息"""
    today = date.today()
    year = today.year
    week_num = int(today.strftime("%W"))
    week_str = f"WR-{year}-W{week_num:02d}"
    date_str = today.strftime("%Y.%m.%d")
    return week_str, date_str


def update_policy_countdown():
    """更新政策倒计时 JSON 文件"""
    log("更新 policy_countdown.json...")
    
    countdown_data = []
    for policy in POLICIES:
        days_left = calculate_days_left(policy["deadline"])
        countdown_data.append({
            "policy": policy["name"],
            "deadline": policy["deadline"].isoformat(),
            "days_left": days_left,
            "urgency": policy["urgency"]
        })
        log(f"  {policy['name']}: {days_left} 天")
    
    with open(POLICY_FILE, "w", encoding="utf-8") as f:
        json.dump(countdown_data, f, ensure_ascii=False, indent=2)
    
    log("policy_countdown.json 更新完成")


def update_index_html():
    """更新 index.html 中的日期和倒计时"""
    log("更新 index.html...")
    
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    week_str, date_str = get_week_info()
    
    # 1. 更新周报标题日期
    # 匹配: WR-2026-W29 | 截至 2026.07.13
    old_pattern = r'WR-\d{4}-W\d{2} \| 截至 \d{4}\.\d{2}\.\d{2}'
    new_header = f'{week_str} | 截至 {date_str}'
    content_new = re.sub(old_pattern, new_header, content)
    if content_new != content:
        log(f"  更新周报标题: {new_header}")
        content = content_new
    
    # 2. 更新倒计时天数 (按顺序匹配)
    # 先获取各政策剩余天数
    days_list = [calculate_days_left(p["deadline"]) for p in POLICIES]
    
    # 使用更精确的模式替换 HTML 中的天数
    # 匹配: <span class="days-num">数字</span>
    days_pattern = r'<span class="days-num">(\d+)</span>'
    matches = list(re.finditer(days_pattern, content))
    
    if len(matches) >= 4:
        # 从后往前替换，避免位置偏移
        for i in range(min(len(matches), len(days_list)) - 1, -1, -1):
            match = matches[i]
            old_days = match.group(1)
            new_days = str(days_list[i])
            if old_days != new_days:
                start, end = match.start(1), match.end(1)
                content = content[:start] + new_days + content[end:]
                log(f"  更新倒计时 {i+1}: {old_days} -> {new_days} 天")
    else:
        log(f"  警告: 只找到 {len(matches)} 个倒计时元素，预期 4 个")
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    log("index.html 更新完成")


def main():
    """主入口"""
    week_str, date_str = get_week_info()
    log("=" * 50)
    log(f"CarbSeek Insight 自动更新开始")
    log(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"目标周报: {week_str}")
    log(f"当前日期: {date_str}")
    log("=" * 50)
    
    try:
        update_policy_countdown()
        update_index_html()
        log("自动更新全部完成")
        return 0
    except Exception as e:
        log(f"错误: {str(e)}")
        import traceback
        log(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main())
