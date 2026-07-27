# CarbSeek Intelligence - 碳足迹研发情报中心 V2.0

> 每周自动追踪全球碳足迹、碳标签、LCA、CBAM、产品碳核算情报

## 🚀 快速访问

- **情报中心 Dashboard**: https://carbseek.github.io/carbseek-insight/intelligence.html
- **原版驾驶舱**: https://carbseek.github.io/carbseek-insight/

## 📋 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  5个Agent   │────▶│  SQLite DB  │────▶│  Dashboard  │
│  自动采集   │     │  数据存储   │     │  可视化展示 │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Agent列表

| Agent | 数据源 | 频率 |
|-------|--------|------|
| BaiduNews-Agent | 百度新闻、百度学术 | 每日2次 |
| CNKI-Agent | 知网、万方、维普 | 每日1次 |
| Patent-Agent | incopat、WIPO、USPTO | 每日1次 |
| Industry-Agent | 行业协会、头部企业 | 每日1次 |
| Policy-Agent | 部委官网、欧盟官网 | 实时/每日 |

## 🛠️ 安装与配置

### 方法一：双击安装（推荐）

1. 打开文件资源管理器，进入 `carbseek-intelligence` 目录
2. **右键** `scheduler.bat` → **以管理员身份运行**
3. 选择 `[1] 安装定时任务`
4. 在 UAC 弹窗中点击 **"是"**

### 方法二：PowerShell 安装

```powershell
# 以管理员身份运行 PowerShell
cd C:\Users\lipen\Documents\Kimi\Workspaces\carbseek\carbseek-intelligence
powershell -ExecutionPolicy Bypass -File setup_schedule.ps1
```

## ⏰ 定时任务说明

| 配置项 | 值 |
|--------|-----|
| **执行时间** | 每周一 10:00 + 每周五 10:00 |
| **执行内容** | 情报采集 → 生成Dashboard → 推送到GitHub |
| **任务名称** | CarbSeekIntelligence_AutoUpdate |

## 🎮 日常使用

双击运行 `scheduler.bat`，选择：

| 选项 | 功能 |
|------|------|
| `1` | 安装/重装定时任务 |
| `2` | **立即手动运行更新** |
| `3` | 查看任务状态和下次执行时间 |
| `4` | 查看最近执行日志 |
| `5` | 删除定时任务 |

## 📁 文件说明

```
carbseek-intelligence/
├── orchestrator.py           # 总控调度器（运行所有Agent）
├── generate_dashboard.py     # Dashboard生成器
├── setup_schedule.ps1        # 定时任务安装脚本
├── scheduler.bat             # 任务管理界面
├── auto_run.bat              # 自动执行脚本（由定时任务调用）
├── database/
│   ├── init_db.py           # 数据库初始化
│   ├── schema.py            # 数据库Schema定义
│   └── carbseek_intel.db    # SQLite数据库
├── agents/
│   ├── base_agent.py        # Agent基类
│   ├── baidu_news_agent.py  # 百度新闻Agent
│   ├── cnki_agent.py        # 学术Agent
│   ├── patent_agent.py      # 专利Agent
│   ├── industry_agent.py    # 行业Agent
│   └── policy_agent.py      # 政策Agent
└── web/
    └── index.html           # 生成的Dashboard
```

## 🔄 手动更新流程

```bash
cd carbseek-intelligence

# 1. 执行情报采集
python orchestrator.py

# 2. 生成Dashboard
python generate_dashboard.py

# 3. 推送到GitHub
copy web\index.html ..\insight-update\intelligence.html
cd ..\insight-update
git add intelligence.html
git commit -m "update: 情报中心更新"
git push origin master:main --force
```

## 📊 数据模型

### 核心表

- **articles** - 新闻/论文/报告情报
- **patents** - 专利数据
- **policies** - 政策/标准
- **projects** - 项目/认证案例
- **companies** - 企业动态
- **weekly_reports** - 周报
- **agent_runs** - Agent运行日志

## 📝 更新日志

### 2026-07-27 V2.0
- ✅ 新增5个Sub-Agent自动采集系统
- ✅ 新增SQLite数据库存储
- ✅ 新增实时Dashboard看板
- ✅ 新增Orchestrator总控调度
- ✅ 配置每周一/五自动更新定时任务

---
© 2026 CarbSeek Intelligence Team
