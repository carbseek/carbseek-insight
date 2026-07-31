// Exports the SQLite database back to the project-root data/*.json files,
// keeping the exact same file layout and field names as the originals.
// Exposes exportAll() for the HTTP API; running the file directly executes it.
const fs = require('node:fs');
const path = require('node:path');
const db = require('../db/connection');

const DATA_DIR = path.join(__dirname, '..', '..', 'data');

const J = (s) => (s == null ? [] : JSON.parse(s));
const B = (v) => v === 1 || v === true;

// Preserve the trailing-newline style of the file being replaced
// (defaults to a trailing newline for new files).
function writeJson(rel, obj) {
  const file = path.join(DATA_DIR, rel);
  let trailing = '\n';
  if (fs.existsSync(file)) {
    const buf = fs.readFileSync(file);
    trailing = buf.length > 0 && buf[buf.length - 1] === 0x0a ? '\n' : '';
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + trailing, 'utf-8');
  return rel;
}

function exportEvidence() {
  const rows = db.prepare('SELECT * FROM evidence ORDER BY rowid').all();
  writeJson('evidence/evidence_pool.json', rows.map((r) => ({
    evidence_id: r.evidence_id,
    title: r.title,
    source: r.source,
    source_url: r.source_url,
    date: r.date,
    industry: r.industry,
    theme: r.theme,
    abstract: r.abstract,
    key_evidence: r.key_evidence,
    agent_explanation: r.agent_explanation,
    credibility: r.credibility,
    in_product_pool: B(r.in_product_pool),
    opportunity_ids: J(r.opportunity_ids),
    evidence_type: r.evidence_type,
  })));
  return rows.length;
}

function exportOpportunities() {
  const rows = db.prepare('SELECT * FROM opportunities ORDER BY rowid').all();
  writeJson('opportunities/opportunity_pool.json', rows.map((r) => ({
    opportunity_id: r.opportunity_id,
    title: r.title,
    industry: r.industry,
    theme: r.theme,
    source_count: r.source_count,
    evidence_grade: r.evidence_grade,
    business_value: r.business_value,
    tech_feasibility: r.tech_feasibility,
    revenue_potential: r.revenue_potential,
    suggested_owner: r.suggested_owner,
    status: r.status,
    priority: r.priority,
    created_at: r.created_at,
    updated_at: r.updated_at,
    evidence_ids: J(r.evidence_ids),
    description: r.description,
    impact_pro: r.impact_pro,
    impact_scan: r.impact_scan,
    impact_db: r.impact_db,
  })));
  return rows.length;
}

function exportRadar() {
  const rows = db.prepare('SELECT * FROM radar_items ORDER BY rowid').all();
  writeJson('radar/this_week.json', rows.map((r) => ({
    radar_id: r.radar_id,
    title: r.title,
    category: r.category,
    severity: r.severity,
    industry: r.industry,
    date: r.date,
    summary: r.summary,
    evidence_ids: J(r.evidence_ids),
    action_required: B(r.action_required),
  })));
  return rows.length;
}

function exportPolicies() {
  const rows = db.prepare('SELECT * FROM policies ORDER BY id').all();
  writeJson('policy_countdown.json', rows.map((r) => {
    const o = {
      policy: r.policy,
      issuing_body: r.issuing_body,
      deadline: r.deadline,
    };
    if (r.days_left != null) o.days_left = r.days_left;
    o.urgency = r.urgency;
    return o;
  }));
  return rows.length;
}

function exportArticles() {
  const rows = db.prepare('SELECT * FROM articles ORDER BY rowid').all();
  writeJson('intelligence/articles.json', rows.map((r) => ({
    article_id: r.article_id,
    title: r.title,
    summary: r.summary,
    source: r.source,
    source_type: r.source_type,
    industry: r.industry,
    publish_date: r.publish_date,
    relevance_score: r.relevance_score,
    url: r.url,
  })));
  return rows.length;
}

function exportCompetitors() {
  const rows = db.prepare('SELECT * FROM competitors ORDER BY id').all();
  writeJson('competitors.json', {
    demo: true,
    competitors: rows.map((r) => ({
      avatar: r.avatar,
      name: r.name,
      action: r.action,
      impact: r.impact,
    })),
  });
  return rows.length;
}

function exportTrends() {
  const rows = db.prepare('SELECT * FROM trends ORDER BY rowid').all();
  const obj = {};
  for (const r of rows) {
    obj[r.industry] = { score: r.score, change: r.change, top_theme: r.top_theme };
  }
  writeJson('industries/trends.json', obj);
  return rows.length;
}

function exportRecommendations() {
  const rows = db.prepare('SELECT * FROM recommendations ORDER BY id').all();
  const obj = {};
  for (const r of rows) {
    if (!obj[r.industry]) obj[r.industry] = [];
    obj[r.industry].push({ type: r.type, name: r.name, desc: r.description });
  }
  writeJson('industries/recommendations.json', obj);
  return rows.length;
}

function exportReports() {
  const rows = db.prepare('SELECT * FROM reports ORDER BY report_id').all();
  for (const r of rows) {
    const o = {
      report_id: r.report_id,
      week_ending: r.week_ending,
    };
    if (r.demo != null) o.demo = B(r.demo);
    o.one_sentence_judgment = r.one_sentence_judgment;
    o.impact_pro = r.impact_pro;
    o.impact_scan = r.impact_scan;
    o.impact_db = r.impact_db;
    o.rd_suggestions = J(r.rd_suggestions);
    if (r.top_opportunities != null) o.top_opportunities = JSON.parse(r.top_opportunities);
    writeJson(path.join('reports', `${r.report_id}.json`), o);
  }
  return rows.length;
}

function exportIntelCenter() {
  const r = db.prepare('SELECT * FROM intel_center WHERE id = 1').get();
  if (!r) return 0;
  writeJson('intel_center.json', {
    demo: B(r.demo),
    overall_status: r.overall_status,
    update_frequency: r.update_frequency,
    agents: J(r.agents),
    stats: J(r.stats),
    latest: J(r.latest),
  });
  return 1;
}

function exportAll() {
  const summary = {
    evidence: exportEvidence(),
    opportunities: exportOpportunities(),
    radar_items: exportRadar(),
    policies: exportPolicies(),
    articles: exportArticles(),
    competitors: exportCompetitors(),
    trends: exportTrends(),
    recommendations: exportRecommendations(),
    reports: exportReports(),
    intel_center: exportIntelCenter(),
  };
  return summary;
}

module.exports = { exportAll };

if (require.main === module) {
  const summary = exportAll();
  console.log('Export complete. Rows written per file:');
  for (const [k, v] of Object.entries(summary)) {
    console.log(`  ${k}: ${v}`);
  }
}
