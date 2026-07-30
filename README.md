# 🌿 CarbSeek Insight

> 碳产业研发情报智能体 | 每周自动追踪全球碳足迹、碳标签、LCA、CBAM、产品碳核算、行业应用、专利和竞品动态

## 🚀 在线访问

```
https://YOUR_USERNAME.github.io/carbseek-insight/
```

## 📸 页面预览

### 首页：本周产业雷达
- 本周重大变化 Top 5
- 产品机会 Top 10
- 政策倒计时
- 行业热度趋势
- 竞品动态
- 研发建议

### 行业页
- 🔬 化工
- 💻 电子电气
- 🚗 汽车
- 🇪🇺 欧盟出口

### 证据库
- 14 条高质量证据，支持按行业/类型/可信度筛选
- 每条含：原文标题、来源、日期、摘要、关键证据、Agent 解释、可信度

### 机会库
- 10 个产品机会按 P0/P1/P2 分级
- 含商业价值、技术可行性、对 Pro/Scan/DB 的影响分析

## 🛠️ 本地开发

```bash
# 启动本地预览(必须通过 http 访问,fetch 不支持 file:// 直接打开)
cd insight
python3 -m http.server 8080

# 浏览器打开 http://localhost:8080
```

## 🔄 数据流(Step A 数据驱动化后)

`index.html` 不再硬编码任何情报内容,页面加载时由 `assets/js/dashboard.js` 读取以下 JSON 并渲染,**JSON 是唯一真相源**:

```
data/reports/WR-2026-W30.json   # 本周判断、研发建议、影响分析、Top10 机会排序
data/radar/this_week.json       # 本周重大变化 Top 5
data/policy_countdown.json      # 政策倒计时(天数由前端按 deadline 实时计算)
data/industries/trends.json     # 行业热度趋势
data/opportunities/opportunity_pool.json  # 机会池(10 条)
data/intel_center.json          # 情报中心状态(演示数据)
data/competitors.json           # 竞品动态(演示数据)
```

更新内容 = 改 JSON,无需动 HTML。其余 6 个页面暂未数据驱动化,后续照搬同模式。

## 📦 部署指南

详见 [DEPLOY.md](DEPLOY.md)

### 快速部署（GitHub Pages）

1. 在 GitHub 创建公开仓库 `carbseek-insight`
2. 运行 `deploy.bat`（Windows）或执行以下命令：

```bash
git remote add origin https://github.com/YOUR_USERNAME/carbseek-insight.git
git push -u origin main
```

3. 在 GitHub Settings → Pages → Source 选择 **GitHub Actions**
4. 等待 1-2 分钟后访问 `https://YOUR_USERNAME.github.io/carbseek-insight/`

## 🔄 每周自动更新

系统已配置 cron job，每周一 08:17 自动：
1. 采集全球碳产业情报
2. 更新证据库和机会库
3. 生成新的 HTML 周报

## 📁 文件结构

```
insight/
├── index.html                  # 首页（本周产业雷达）
├── industry-chemical.html      # 化工行业页
├── industry-electronics.html   # 电子电气行业页
├── industry-automotive.html    # 汽车行业页
├── industry-eu-export.html     # 欧盟出口行业页
├── evidence.html               # 证据库
├── opportunities.html          # 机会库
├── data/
│   ├── schema.json             # 数据模型定义
│   ├── evidence/               # 证据数据
│   ├── opportunities/          # 机会数据
│   ├── radar/                  # 雷达数据
│   └── reports/                # 周报数据
├── scripts/
│   └── insight_engine.py       # 情报采集引擎
└── .github/workflows/
    └── pages.yml               # GitHub Actions 自动部署
```

## 📝 数据来源

- 欧盟官方公报、European Commission TAXUD
- Nature Communications、IEEE、Transportation Research
- 企业年报/ESG报告（巴斯夫、宁德时代、三星等）
- 行业协会（ACEA、中国机电商会等）
- 竞品动态（碳阻迹、妙盈科技、MSCI 等）

## 📄 License

© 2026 CarbSeek. All rights reserved.
