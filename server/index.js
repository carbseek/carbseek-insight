// CarbSeek Insight local backend.
// Express + node:sqlite. data/*.json is seeded into SQLite (scripts/import_json.js)
// and can be exported back (scripts/export_json.js) so a git push syncs the site.
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const jwt = require('jsonwebtoken');
const db = require('./db/connection');
const { verifyPassword, findUser, ensureAdminSeed } = require('./db/users');
const { exportAll } = require('./scripts/export_json');

const PORT = Number(process.env.PORT) || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'dev-only-insecure-secret';
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'changeme';

// Seed the initial admin account (default admin/admin123) on first run.
if (ensureAdminSeed()) console.log('Seeded initial admin user in users table');

const app = express();
app.use(express.json());

// --- CORS: wide open for local development (no cors package) ---
app.use((req, res, next) => {
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// --- Static admin SPA (next phase); skip silently if not built yet ---
const adminDist = path.join(__dirname, '..', 'admin', 'dist');
if (fs.existsSync(adminDist)) {
  app.use('/admin', express.static(adminDist));
}

// --- Auth ---
function authMiddleware(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'missing token' });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: 'invalid or expired token' });
  }
}

app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body || {};
  const user = username ? findUser(username) : null;
  // DB users table first; fall back to env-var credentials for backward compatibility.
  const ok = user
    ? verifyPassword(password, user.password_hash)
    : (username === ADMIN_USERNAME && password === ADMIN_PASSWORD);
  if (!ok) return res.status(401).json({ error: 'invalid credentials' });
  const token = jwt.sign({ sub: username, role: user?.role || 'admin' }, JWT_SECRET, { expiresIn: '7d' });
  res.json({ token, expires_in: '7d' });
});

// --- Row (de)serialization helpers ---
function parseRow(row, cfg) {
  if (!row) return row;
  const out = { ...row };
  for (const col of cfg.json || []) out[col] = out[col] == null ? [] : JSON.parse(out[col]);
  for (const col of cfg.bool || []) out[col] = out[col] === 1;
  if (cfg.alias) for (const [api, col] of Object.entries(cfg.alias)) {
    out[api] = out[col];
    delete out[col];
  }
  return out;
}

function serializeBody(body, cfg) {
  const row = {};
  for (const col of cfg.columns) {
    const apiName = cfg.aliasRev?.[col] || col;
    if (body[apiName] === undefined) continue;
    let v = body[apiName];
    if ((cfg.json || []).includes(col)) v = JSON.stringify(v ?? []);
    else if ((cfg.bool || []).includes(col)) v = v ? 1 : 0;
    row[col] = v;
  }
  return row;
}

// --- Entity configs for generic CRUD ---
const ENTITIES = {
  evidence: {
    table: 'evidence', pk: 'evidence_id',
    columns: ['evidence_id', 'title', 'source', 'source_url', 'date', 'industry', 'theme',
      'abstract', 'key_evidence', 'agent_explanation', 'credibility', 'in_product_pool',
      'opportunity_ids', 'evidence_type'],
    json: ['opportunity_ids'], bool: ['in_product_pool'],
    required: ['evidence_id', 'title'],
    filters: { industry: 'industry', type: 'evidence_type', credibility: 'credibility' },
  },
  opportunities: {
    table: 'opportunities', pk: 'opportunity_id',
    columns: ['opportunity_id', 'title', 'industry', 'theme', 'source_count', 'evidence_grade',
      'business_value', 'tech_feasibility', 'revenue_potential', 'suggested_owner', 'status',
      'priority', 'created_at', 'updated_at', 'evidence_ids', 'description', 'impact_pro',
      'impact_scan', 'impact_db'],
    json: ['evidence_ids'],
    required: ['opportunity_id', 'title'],
    filters: { priority: 'priority', industry: 'industry' },
  },
  radar_items: {
    table: 'radar_items', pk: 'radar_id',
    columns: ['radar_id', 'title', 'category', 'severity', 'industry', 'date', 'summary',
      'evidence_ids', 'action_required'],
    json: ['evidence_ids'], bool: ['action_required'],
    required: ['radar_id', 'title'],
    filters: { category: 'category', severity: 'severity', industry: 'industry' },
  },
  policies: {
    table: 'policies', pk: 'id', autoId: true,
    columns: ['policy', 'issuing_body', 'deadline', 'days_left', 'urgency'],
    required: ['policy', 'deadline'],
    filters: { urgency: 'urgency' },
  },
  articles: {
    table: 'articles', pk: 'article_id',
    columns: ['article_id', 'title', 'summary', 'source', 'source_type', 'industry',
      'publish_date', 'relevance_score', 'url'],
    required: ['article_id', 'title'],
    filters: { source_type: 'source_type', industry: 'industry' },
  },
  competitors: {
    table: 'competitors', pk: 'id', autoId: true,
    columns: ['avatar', 'name', 'action', 'impact'],
    required: ['name'],
  },
  trends: {
    table: 'trends', pk: 'industry',
    columns: ['industry', 'score', 'change', 'top_theme'],
    required: ['industry'],
  },
  recommendations: {
    table: 'recommendations', pk: 'id', autoId: true,
    columns: ['industry', 'type', 'name', 'description'],
    alias: { desc: 'description' },
    aliasRev: { description: 'desc' },
    required: ['industry', 'type', 'name'],
    filters: { industry: 'industry', type: 'type' },
  },
};

function listRows(cfg, query) {
  const where = [];
  const params = [];
  for (const [qp, col] of Object.entries(cfg.filters || {})) {
    if (query[qp] !== undefined && query[qp] !== '') {
      where.push(`${col} = ?`);
      params.push(query[qp]);
    }
  }
  const sql = `SELECT * FROM ${cfg.table}${where.length ? ' WHERE ' + where.join(' AND ') : ''} ORDER BY rowid`;
  return db.prepare(sql).all(...params).map((r) => parseRow(r, cfg));
}

function mountCrud(name, cfg) {
  app.post(`/api/${name}`, authMiddleware, (req, res) => {
    const body = req.body || {};
    for (const f of cfg.required) {
      if (body[f] === undefined || body[f] === null || body[f] === '') {
        return res.status(400).json({ error: `missing required field: ${f}` });
      }
    }
    const row = serializeBody(body, cfg);
    const cols = Object.keys(row);
    try {
      const info = db.prepare(
        `INSERT INTO ${cfg.table} (${cols.join(', ')}) VALUES (${cols.map(() => '?').join(', ')})`
      ).run(...cols.map((c) => row[c]));
      const pkVal = cfg.autoId ? info.lastInsertRowid : row[cfg.pk];
      const created = db.prepare(`SELECT * FROM ${cfg.table} WHERE ${cfg.pk} = ?`).get(pkVal);
      res.status(201).json(parseRow(created, cfg));
    } catch (e) {
      if (String(e.message).includes('UNIQUE')) {
        return res.status(409).json({ error: `${cfg.pk} already exists` });
      }
      throw e;
    }
  });

  app.put(`/api/${name}/:id`, authMiddleware, (req, res) => {
    const existing = db.prepare(`SELECT * FROM ${cfg.table} WHERE ${cfg.pk} = ?`).get(req.params.id);
    if (!existing) return res.status(404).json({ error: `${name} not found` });
    const row = serializeBody(req.body || {}, cfg);
    delete row[cfg.pk];
    const cols = Object.keys(row);
    if (cols.length === 0) return res.status(400).json({ error: 'no updatable fields provided' });
    db.prepare(
      `UPDATE ${cfg.table} SET ${cols.map((c) => `${c} = ?`).join(', ')} WHERE ${cfg.pk} = ?`
    ).run(...cols.map((c) => row[c]), req.params.id);
    res.json(parseRow(db.prepare(`SELECT * FROM ${cfg.table} WHERE ${cfg.pk} = ?`).get(req.params.id), cfg));
  });

  app.delete(`/api/${name}/:id`, authMiddleware, (req, res) => {
    const info = db.prepare(`DELETE FROM ${cfg.table} WHERE ${cfg.pk} = ?`).run(req.params.id);
    if (info.changes === 0) return res.status(404).json({ error: `${name} not found` });
    res.json({ deleted: req.params.id });
  });
}

for (const [name, cfg] of Object.entries(ENTITIES)) mountCrud(name, cfg);

// --- Public read endpoints ---
app.get('/api/evidence', (req, res) => res.json(listRows(ENTITIES.evidence, req.query)));
app.get('/api/opportunities', (req, res) => res.json(listRows(ENTITIES.opportunities, req.query)));
app.get('/api/radar-items', (req, res) => res.json(listRows(ENTITIES.radar_items, req.query)));
app.get('/api/policies', (req, res) => res.json(listRows(ENTITIES.policies, req.query)));
app.get('/api/articles', (req, res) => res.json(listRows(ENTITIES.articles, req.query)));
app.get('/api/competitors', (req, res) => {
  res.json({ demo: true, competitors: listRows(ENTITIES.competitors, req.query) });
});
app.get('/api/trends', (req, res) => {
  const obj = {};
  for (const r of listRows(ENTITIES.trends, req.query)) {
    obj[r.industry] = { score: r.score, change: r.change, top_theme: r.top_theme };
  }
  res.json(obj);
});
app.get('/api/recommendations', (req, res) => {
  const obj = {};
  for (const r of listRows(ENTITIES.recommendations, req.query)) {
    if (!obj[r.industry]) obj[r.industry] = [];
    obj[r.industry].push({ id: r.id, type: r.type, name: r.name, desc: r.desc });
  }
  res.json(obj);
});

function parseReport(row) {
  if (!row) return row;
  const out = { ...row };
  for (const col of ['rd_suggestions', 'top_opportunities']) {
    if (out[col] != null) out[col] = JSON.parse(out[col]);
  }
  if (out.demo != null) out.demo = out.demo === 1;
  return out;
}

function getReport(reportId) {
  const row = reportId
    ? db.prepare('SELECT * FROM reports WHERE report_id = ?').get(reportId)
    : db.prepare('SELECT * FROM reports ORDER BY week_ending DESC, report_id DESC LIMIT 1').get();
  return parseReport(row);
}

app.get('/api/reports', (req, res) => {
  const rows = db.prepare('SELECT * FROM reports ORDER BY report_id DESC').all();
  res.json(rows.map(parseReport));
});

app.get('/api/reports/latest', (req, res) => {
  const report = getReport();
  if (!report) return res.status(404).json({ error: 'no reports' });
  res.json(report);
});

app.get('/api/intel-center', (req, res) => {
  const row = db.prepare('SELECT * FROM intel_center WHERE id = 1').get();
  if (!row) return res.status(404).json({ error: 'intel_center not initialized' });
  res.json({
    demo: row.demo === 1,
    overall_status: row.overall_status,
    update_frequency: row.update_frequency,
    agents: JSON.parse(row.agents || '[]'),
    stats: JSON.parse(row.stats || '[]'),
    latest: JSON.parse(row.latest || '[]'),
  });
});

// Aggregate matching the shape the dashboard renderer consumes.
app.get('/api/dashboard', (req, res) => {
  res.json({
    report: getReport(),
    radar: listRows(ENTITIES.radar_items, {}),
    countdown: listRows(ENTITIES.policies, {}),
    trends: (() => {
      const obj = {};
      for (const r of listRows(ENTITIES.trends, {})) {
        obj[r.industry] = { score: r.score, change: r.change, top_theme: r.top_theme };
      }
      return obj;
    })(),
    opportunities: listRows(ENTITIES.opportunities, {}),
    intelCenter: (() => {
      const row = db.prepare('SELECT * FROM intel_center WHERE id = 1').get();
      if (!row) return null;
      return {
        demo: row.demo === 1,
        overall_status: row.overall_status,
        update_frequency: row.update_frequency,
        agents: JSON.parse(row.agents || '[]'),
        stats: JSON.parse(row.stats || '[]'),
        latest: JSON.parse(row.latest || '[]'),
      };
    })(),
    competitors: { demo: true, competitors: listRows(ENTITIES.competitors, {}) },
  });
});

// --- Reports write endpoints (keyed by report_id) ---
const REPORT_COLS = ['report_id', 'week_ending', 'one_sentence_judgment', 'impact_pro',
  'impact_scan', 'impact_db', 'rd_suggestions', 'top_opportunities', 'demo'];

function serializeReport(body) {
  const row = {};
  for (const col of REPORT_COLS) {
    if (body[col] === undefined) continue;
    let v = body[col];
    if (col === 'rd_suggestions' || col === 'top_opportunities') v = JSON.stringify(v ?? []);
    else if (col === 'demo') v = v ? 1 : 0;
    row[col] = v;
  }
  return row;
}

app.post('/api/reports', authMiddleware, (req, res) => {
  const body = req.body || {};
  for (const f of ['report_id', 'week_ending']) {
    if (!body[f]) return res.status(400).json({ error: `missing required field: ${f}` });
  }
  const row = serializeReport(body);
  const cols = Object.keys(row);
  try {
    db.prepare(`INSERT INTO reports (${cols.join(', ')}) VALUES (${cols.map(() => '?').join(', ')})`)
      .run(...cols.map((c) => row[c]));
  } catch (e) {
    if (String(e.message).includes('UNIQUE')) {
      return res.status(409).json({ error: 'report_id already exists' });
    }
    throw e;
  }
  res.status(201).json(getReport(body.report_id));
});

app.put('/api/reports/:report_id', authMiddleware, (req, res) => {
  if (!getReport(req.params.report_id)) return res.status(404).json({ error: 'report not found' });
  const row = serializeReport(req.body || {});
  delete row.report_id;
  const cols = Object.keys(row);
  if (cols.length === 0) return res.status(400).json({ error: 'no updatable fields provided' });
  db.prepare(`UPDATE reports SET ${cols.map((c) => `${c} = ?`).join(', ')} WHERE report_id = ?`)
    .run(...cols.map((c) => row[c]), req.params.report_id);
  res.json(getReport(req.params.report_id));
});

app.delete('/api/reports/:report_id', authMiddleware, (req, res) => {
  const info = db.prepare('DELETE FROM reports WHERE report_id = ?').run(req.params.report_id);
  if (info.changes === 0) return res.status(404).json({ error: 'report not found' });
  res.json({ deleted: req.params.report_id });
});

// --- intel_center write (single-row table) ---
app.put('/api/intel-center', authMiddleware, (req, res) => {
  const body = req.body || {};
  const cols = [];
  const params = [];
  for (const col of ['overall_status', 'update_frequency']) {
    if (body[col] !== undefined) { cols.push(`${col} = ?`); params.push(body[col]); }
  }
  for (const col of ['agents', 'stats', 'latest']) {
    if (body[col] !== undefined) { cols.push(`${col} = ?`); params.push(JSON.stringify(body[col] ?? [])); }
  }
  if (body.demo !== undefined) { cols.push('demo = ?'); params.push(body.demo ? 1 : 0); }
  if (cols.length === 0) return res.status(400).json({ error: 'no updatable fields provided' });
  const existing = db.prepare('SELECT id FROM intel_center WHERE id = 1').get();
  if (!existing) {
    db.prepare('INSERT INTO intel_center (id, overall_status, update_frequency, agents, stats, latest, demo) VALUES (1, ?, ?, ?, ?, ?, ?)')
      .run(body.overall_status ?? null, body.update_frequency ?? null,
        JSON.stringify(body.agents ?? []), JSON.stringify(body.stats ?? []),
        JSON.stringify(body.latest ?? []), body.demo ? 1 : 0);
  } else {
    db.prepare(`UPDATE intel_center SET ${cols.join(', ')} WHERE id = 1`).run(...params);
  }
  const row = db.prepare('SELECT * FROM intel_center WHERE id = 1').get();
  res.json({
    demo: row.demo === 1,
    overall_status: row.overall_status,
    update_frequency: row.update_frequency,
    agents: JSON.parse(row.agents || '[]'),
    stats: JSON.parse(row.stats || '[]'),
    latest: JSON.parse(row.latest || '[]'),
  });
});

// --- Export DB back to data/*.json ---
app.post('/api/admin/export', authMiddleware, (req, res) => {
  try {
    const summary = exportAll();
    res.json({ ok: true, summary });
  } catch (e) {
    res.status(500).json({ error: `export failed: ${e.message}` });
  }
});

// --- Health + 404 + error handling ---
app.get('/api/health', (req, res) => res.json({ ok: true }));

app.use('/api', (req, res) => res.status(404).json({ error: 'not found' }));

app.use((err, req, res, next) => {
  if (err?.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'invalid JSON body' });
  }
  console.error(err);
  res.status(500).json({ error: 'internal server error' });
});

app.listen(PORT, () => {
  console.log(`CarbSeek Insight server listening on http://localhost:${PORT}`);
});
