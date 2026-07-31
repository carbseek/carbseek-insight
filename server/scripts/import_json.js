// Seeds the SQLite database from the project-root data/*.json files.
// Full reload: clears every table first, so the script is idempotent.
const fs = require('node:fs');
const path = require('node:path');
const db = require('../db/connection');

const DATA_DIR = path.join(__dirname, '..', '..', 'data');

function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, rel), 'utf-8'));
}

const J = (v) => JSON.stringify(v ?? []);
const B = (v) => (v ? 1 : 0);

function importEvidence() {
  const rows = readJson('evidence/evidence_pool.json');
  const stmt = db.prepare(`INSERT INTO evidence
    (evidence_id, title, source, source_url, date, industry, theme, abstract,
     key_evidence, agent_explanation, credibility, in_product_pool, opportunity_ids, evidence_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  for (const r of rows) {
    stmt.run(r.evidence_id, r.title, r.source, r.source_url, r.date, r.industry, r.theme,
      r.abstract, r.key_evidence, r.agent_explanation, r.credibility,
      B(r.in_product_pool), J(r.opportunity_ids), r.evidence_type);
  }
  return rows.length;
}

function importOpportunities() {
  const rows = readJson('opportunities/opportunity_pool.json');
  const stmt = db.prepare(`INSERT INTO opportunities
    (opportunity_id, title, industry, theme, source_count, evidence_grade, business_value,
     tech_feasibility, revenue_potential, suggested_owner, status, priority, created_at,
     updated_at, evidence_ids, description, impact_pro, impact_scan, impact_db)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  for (const r of rows) {
    stmt.run(r.opportunity_id, r.title, r.industry, r.theme, r.source_count, r.evidence_grade,
      r.business_value, r.tech_feasibility, r.revenue_potential, r.suggested_owner, r.status,
      r.priority, r.created_at, r.updated_at, J(r.evidence_ids), r.description,
      r.impact_pro, r.impact_scan, r.impact_db);
  }
  return rows.length;
}

function importRadar() {
  const rows = readJson('radar/this_week.json');
  const stmt = db.prepare(`INSERT INTO radar_items
    (radar_id, title, category, severity, industry, date, summary, evidence_ids, action_required)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  for (const r of rows) {
    stmt.run(r.radar_id, r.title, r.category, r.severity, r.industry, r.date,
      r.summary, J(r.evidence_ids), B(r.action_required));
  }
  return rows.length;
}

function importPolicies() {
  const rows = readJson('policy_countdown.json');
  const stmt = db.prepare(`INSERT INTO policies (policy, issuing_body, deadline, days_left, urgency)
    VALUES (?, ?, ?, ?, ?)`);
  for (const r of rows) {
    stmt.run(r.policy, r.issuing_body, r.deadline, r.days_left ?? null, r.urgency);
  }
  return rows.length;
}

function importArticles() {
  const rows = readJson('intelligence/articles.json');
  const stmt = db.prepare(`INSERT INTO articles
    (article_id, title, summary, source, source_type, industry, publish_date, relevance_score, url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  for (const r of rows) {
    stmt.run(r.article_id, r.title, r.summary, r.source, r.source_type, r.industry,
      r.publish_date, r.relevance_score, r.url);
  }
  return rows.length;
}

function importCompetitors() {
  const { competitors } = readJson('competitors.json');
  const stmt = db.prepare(`INSERT INTO competitors (avatar, name, action, impact) VALUES (?, ?, ?, ?)`);
  for (const r of competitors) {
    stmt.run(r.avatar, r.name, r.action, r.impact);
  }
  return competitors.length;
}

function importTrends() {
  const obj = readJson('industries/trends.json');
  const stmt = db.prepare(`INSERT INTO trends (industry, score, change, top_theme) VALUES (?, ?, ?, ?)`);
  let n = 0;
  for (const [industry, r] of Object.entries(obj)) {
    stmt.run(industry, r.score, r.change, r.top_theme);
    n++;
  }
  return n;
}

function importRecommendations() {
  const obj = readJson('industries/recommendations.json');
  const stmt = db.prepare(`INSERT INTO recommendations (industry, type, name, description) VALUES (?, ?, ?, ?)`);
  let n = 0;
  for (const [industry, rows] of Object.entries(obj)) {
    for (const r of rows) {
      stmt.run(industry, r.type, r.name, r.desc);
      n++;
    }
  }
  return n;
}

function importReports() {
  const dir = path.join(DATA_DIR, 'reports');
  const files = fs.readdirSync(dir).filter((f) => /^WR-.*\.json$/.test(f)).sort();
  const stmt = db.prepare(`INSERT INTO reports
    (report_id, week_ending, one_sentence_judgment, impact_pro, impact_scan, impact_db,
     rd_suggestions, top_opportunities, demo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  for (const f of files) {
    const r = readJson(path.join('reports', f));
    stmt.run(r.report_id, r.week_ending, r.one_sentence_judgment, r.impact_pro, r.impact_scan,
      r.impact_db, J(r.rd_suggestions),
      r.top_opportunities == null ? null : JSON.stringify(r.top_opportunities),
      r.demo == null ? null : B(r.demo));
  }
  return files.length;
}

function importIntelCenter() {
  const r = readJson('intel_center.json');
  db.prepare(`INSERT INTO intel_center (id, overall_status, update_frequency, agents, stats, latest, demo)
    VALUES (1, ?, ?, ?, ?, ?, ?)`)
    .run(r.overall_status, r.update_frequency, J(r.agents), J(r.stats), J(r.latest), B(r.demo));
  return 1;
}

function main() {
  const tables = ['evidence', 'opportunities', 'radar_items', 'policies', 'articles',
    'competitors', 'trends', 'reports', 'recommendations', 'intel_center'];
  for (const t of tables) db.exec(`DELETE FROM ${t};`);

  const counts = {
    evidence: importEvidence(),
    opportunities: importOpportunities(),
    radar_items: importRadar(),
    policies: importPolicies(),
    articles: importArticles(),
    competitors: importCompetitors(),
    trends: importTrends(),
    reports: importReports(),
    recommendations: importRecommendations(),
    intel_center: importIntelCenter(),
  };

  console.log('Import complete. Row counts:');
  for (const [t, n] of Object.entries(counts)) {
    const inDb = db.prepare(`SELECT COUNT(*) AS c FROM ${t}`).get().c;
    console.log(`  ${t}: ${n} imported, ${inDb} in db`);
  }
}

main();
