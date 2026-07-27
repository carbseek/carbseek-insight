"""
CarbSeek Intelligence - 数据库Schema定义
=====================================
SQLite + pgvector兼容层
"""

SCHEMA_SQL = """
-- ============================================
-- 核心情报数据表
-- ============================================

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT UNIQUE NOT NULL,           -- 业务ID: ART-{timestamp}-{hash}
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    source TEXT NOT NULL,                       -- 来源站点
    source_type TEXT CHECK(source_type IN ('news','academic','patent','policy','industry')),
    publish_date DATE,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 分类标签
    industry TEXT,                              -- 电气电子|化工|汽车|外贸|通用
    topic TEXT,                                 -- 碳足迹|碳标签|LCA|CBAM|EPD|PCR|Scope3
    
    -- 质量评分
    relevance_score REAL DEFAULT 0.0,           -- 相关度 0-1
    evidence_grade TEXT CHECK(evidence_grade IN ('A','B','C','D')),
    
    -- 状态
    status TEXT DEFAULT 'new' CHECK(status IN ('new','reviewed','featured','archived')),
    is_weekly_reported BOOLEAN DEFAULT FALSE,
    
    -- 元数据
    author TEXT,
    keywords TEXT,                              -- JSON数组
    doi TEXT,
    language TEXT DEFAULT 'zh',
    
    -- 向量化字段（文本存储，实际用pgvector时为vector类型）
    embedding TEXT,                             -- JSON格式向量
    
    -- 原始数据保留
    raw_data TEXT                               -- JSON原始数据
);

CREATE TABLE IF NOT EXISTS patents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT UNIQUE NOT NULL,             -- 专利号
    title TEXT NOT NULL,
    abstract TEXT,
    applicant TEXT,                             -- 申请人
    inventor TEXT,
    
    -- 分类
    ipc_classification TEXT,                    -- IPC分类号
    patent_type TEXT CHECK(patent_type IN ('invention','utility','design')),
    
    -- 时间
    application_date DATE,
    publication_date DATE,
    grant_date DATE,
    
    -- 法律状态
    legal_status TEXT CHECK(legal_status IN ('pending','granted','rejected','expired')),
    
    -- 评分
    relevance_score REAL DEFAULT 0.0,
    carbseek_value TEXT CHECK(carbseek_value IN ('high','medium','low')),
    
    source TEXT,                                -- 数据源: incopat/WIPO/USPTO/EPO
    url TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,                               -- 政策全文或摘要
    
    -- 来源
    issuing_body TEXT NOT NULL,                 -- 发布机构
    policy_type TEXT CHECK(policy_type IN ('national','industry','international','standard')),
    region TEXT,                                -- 中国|欧盟|美国|韩国|日本
    
    -- 时间
    publish_date DATE,
    effective_date DATE,
    deadline_date DATE,                         -- 截止日期（如有）
    days_left INTEGER,                          -- 剩余天数
    
    -- 影响评估
    impact_level TEXT CHECK(impact_level IN ('critical','high','medium','low')),
    affected_industries TEXT,                   -- JSON数组
    carbseek_action TEXT,                       -- 建议行动
    
    status TEXT DEFAULT 'active' CHECK(status IN ('draft','active','expired','updated')),
    url TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT,                               -- 企业名称
    industry TEXT,
    
    project_type TEXT CHECK(project_type IN ('certification','pilot','standard','platform','partnership')),
    description TEXT,
    
    -- 状态
    status TEXT DEFAULT 'ongoing' CHECK(status IN ('planned','ongoing','completed','cancelled')),
    
    -- 时间
    start_date DATE,
    end_date DATE,
    announcement_date DATE,
    
    relevance_score REAL DEFAULT 0.0,
    source TEXT,
    url TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    industry TEXT,
    country TEXT,
    
    -- 动态
    action_type TEXT CHECK(action_type IN ('certification','product_launch','partnership','investment','policy_response')),
    action_description TEXT,
    action_date DATE,
    
    relevance_score REAL DEFAULT 0.0,
    source TEXT,
    url TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 情报分析表
-- ============================================

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE NOT NULL,             -- WR-YYYY-WXX
    week_start DATE,
    week_end DATE,
    
    -- 核心内容
    one_sentence_judgment TEXT,
    key_changes TEXT,                           -- JSON: Top 5变化
    opportunities TEXT,                         -- JSON: Top 10机会
    risks TEXT,                                 -- JSON: 风险预警
    
    -- 统计
    article_count INTEGER DEFAULT 0,
    patent_count INTEGER DEFAULT 0,
    policy_count INTEGER DEFAULT 0,
    
    -- 产品影响
    impact_pro TEXT,
    impact_scan TEXT,
    impact_db TEXT,
    
    -- 研发建议
    rd_suggestions TEXT,                        -- JSON数组
    
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS keyword_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    industry TEXT,
    source_type TEXT,
    UNIQUE(keyword, date, industry, source_type)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('running','success','failed','partial')),
    items_collected INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER
);

-- ============================================
-- 索引
-- ============================================

CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(publish_date);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_type, industry);
CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);

CREATE INDEX IF NOT EXISTS idx_patents_date ON patents(publication_date);
CREATE INDEX IF NOT EXISTS idx_patents_applicant ON patents(applicant);
CREATE INDEX IF NOT EXISTS idx_patents_ipc ON patents(ipc_classification);

CREATE INDEX IF NOT EXISTS idx_policies_date ON policies(publish_date);
CREATE INDEX IF NOT EXISTS idx_policies_deadline ON policies(deadline_date);
CREATE INDEX IF NOT EXISTS idx_policies_impact ON policies(impact_level);

CREATE INDEX IF NOT EXISTS idx_keyword_trends ON keyword_trends(keyword, date);

-- ============================================
-- 视图
-- ============================================

CREATE VIEW IF NOT EXISTS v_high_value_articles AS
SELECT * FROM articles 
WHERE relevance_score >= 0.7 
  AND status != 'archived'
ORDER BY relevance_score DESC, publish_date DESC;

CREATE VIEW IF NOT EXISTS v_upcoming_policies AS
SELECT * FROM policies 
WHERE deadline_date IS NOT NULL 
  AND days_left <= 180
  AND status = 'active'
ORDER BY days_left ASC;

CREATE VIEW IF NOT EXISTS v_weekly_stats AS
SELECT 
    date(collected_at) as collect_date,
    source_type,
    industry,
    COUNT(*) as count
FROM articles
GROUP BY date(collected_at), source_type, industry
ORDER BY collect_date DESC;
"""

# 初始化数据 - 政策倒计时
INITIAL_POLICIES = [
    {
        "policy_id": "POL-2026-001",
        "title": "CBAM 正式征收（取消免费配额）",
        "issuing_body": "European Commission",
        "policy_type": "international",
        "region": "欧盟",
        "publish_date": "2023-05-10",
        "effective_date": "2026-10-01",
        "deadline_date": "2026-10-01",
        "days_left": 66,
        "impact_level": "critical",
        "affected_industries": '["钢铁","水泥","化肥","铝","电力","氢"]',
        "carbseek_action": "紧急：完成CBAM申报模块开发",
        "url": "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en"
    },
    {
        "policy_id": "POL-2026-002",
        "title": "韩国电子电气碳标签强制实施",
        "issuing_body": "韩国产业通商资源部",
        "policy_type": "international",
        "region": "韩国",
        "publish_date": "2023-04-18",
        "effective_date": "2026-12-31",
        "deadline_date": "2026-12-31",
        "days_left": 157,
        "impact_level": "high",
        "affected_industries": '["电子电气","家电","IT设备"]',
        "carbseek_action": "开发韩国碳标签对接模块",
        "url": "https://www.motie.go.kr/"
    },
    {
        "policy_id": "POL-2026-003",
        "title": "欧盟新电池法规碳足迹强制声明",
        "issuing_body": "European Parliament",
        "policy_type": "international",
        "region": "欧盟",
        "publish_date": "2023-07-12",
        "effective_date": "2027-02-18",
        "deadline_date": "2027-02-18",
        "days_left": 206,
        "impact_level": "critical",
        "affected_industries": '["动力电池","储能电池","汽车"]',
        "carbseek_action": "电池碳足迹核算工具开发",
        "url": "https://eur-lex.europa.eu/eli/reg/2023/1542"
    },
    {
        "policy_id": "POL-2026-004",
        "title": "CBAM 扩大至有机化学品、塑料",
        "issuing_body": "European Commission",
        "policy_type": "international",
        "region": "欧盟",
        "publish_date": "2025-08-01",
        "effective_date": "2027-01-01",
        "deadline_date": "2027-01-01",
        "days_left": 158,
        "impact_level": "high",
        "affected_industries": '["化工","塑料","制药"]',
        "carbseek_action": "扩展化工行业因子库",
        "url": "https://taxation-customs.ec.europa.eu/"
    }
]
