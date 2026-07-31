-- CarbSeek Insight local database schema
-- Array-typed fields are stored as TEXT containing JSON strings.

CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  title TEXT,
  source TEXT,
  source_url TEXT,
  date TEXT,
  industry TEXT,
  theme TEXT,
  abstract TEXT,
  key_evidence TEXT,
  agent_explanation TEXT,
  credibility TEXT,
  in_product_pool INTEGER DEFAULT 0,
  opportunity_ids TEXT,
  evidence_type TEXT
);

CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id TEXT PRIMARY KEY,
  title TEXT,
  industry TEXT,
  theme TEXT,
  source_count INTEGER,
  evidence_grade TEXT,
  business_value INTEGER,
  tech_feasibility INTEGER,
  revenue_potential TEXT,
  suggested_owner TEXT,
  status TEXT,
  priority TEXT,
  created_at TEXT,
  updated_at TEXT,
  evidence_ids TEXT,
  description TEXT,
  impact_pro TEXT,
  impact_scan TEXT,
  impact_db TEXT
);

CREATE TABLE IF NOT EXISTS radar_items (
  radar_id TEXT PRIMARY KEY,
  title TEXT,
  category TEXT,
  severity TEXT,
  industry TEXT,
  date TEXT,
  summary TEXT,
  evidence_ids TEXT,
  action_required INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  policy TEXT,
  issuing_body TEXT,
  deadline TEXT,
  days_left INTEGER,
  urgency TEXT
);

CREATE TABLE IF NOT EXISTS articles (
  article_id TEXT PRIMARY KEY,
  title TEXT,
  summary TEXT,
  source TEXT,
  source_type TEXT,
  industry TEXT,
  publish_date TEXT,
  relevance_score REAL,
  url TEXT
);

CREATE TABLE IF NOT EXISTS competitors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  avatar TEXT,
  name TEXT,
  action TEXT,
  impact TEXT
);

CREATE TABLE IF NOT EXISTS trends (
  industry TEXT PRIMARY KEY,
  score INTEGER,
  change INTEGER,
  top_theme TEXT
);

CREATE TABLE IF NOT EXISTS reports (
  report_id TEXT PRIMARY KEY,
  week_ending TEXT,
  one_sentence_judgment TEXT,
  impact_pro TEXT,
  impact_scan TEXT,
  impact_db TEXT,
  rd_suggestions TEXT,
  top_opportunities TEXT,
  demo INTEGER
);

CREATE TABLE IF NOT EXISTS recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  industry TEXT,
  type TEXT,
  name TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'admin',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS intel_center (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  overall_status TEXT,
  update_frequency TEXT,
  agents TEXT,
  stats TEXT,
  latest TEXT,
  demo INTEGER
);
