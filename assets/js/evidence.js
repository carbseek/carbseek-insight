/**
 * CarbSeek Insight - 证据库渲染器
 * 从 data/*.json 加载数据并渲染证据卡片与筛选器,JSON 为唯一真相源。
 * 无依赖,原生 ES6,GitHub Pages 纯静态可用。
 */
(function () {
  'use strict';

  var DATA = {
    evidence: 'data/evidence/evidence_pool.json',
    opportunities: 'data/opportunities/opportunity_pool.json',
    report: 'data/reports/WR-2026-W30.json'
  };

  var TYPE_CLASS = {
    '政策': 'type-policy',
    '学术': 'type-academic',
    '专利': 'type-patent',
    '竞品': 'type-competitor',
    '行业应用': 'type-industry'
  };
  var CRED_CLASS = { '高': 'cred-high', '中': 'cred-medium', '低': 'cred-low' };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function $(id) { return document.getElementById(id); }

  function fail(id) {
    var el = $(id);
    if (el) el.innerHTML = '<div style="padding:16px;font-size:12px;color:var(--text-secondary);">数据加载失败,请稍后刷新重试。</div>';
  }

  function loadJson(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' -> ' + r.status);
      return r.json();
    });
  }

  /* ===== 报头:WR 编号 + 证据总数 ===== */
  function renderMeta(report, total) {
    var meta = $('report-meta');
    if (meta) meta.textContent = report.report_id;
    var el = $('evidence-total');
    if (el) el.textContent = '共 ' + total + ' 条证据';
  }

  /* ===== 筛选下拉:选项由数据动态生成 ===== */
  function renderFilterOptions(evidence) {
    var defs = [
      { id: 'filter-industry', key: 'industry', all: '全部行业' },
      { id: 'filter-type', key: 'evidence_type', all: '全部类型' },
      { id: 'filter-credibility', key: 'credibility', all: '全部可信度' }
    ];
    defs.forEach(function (d) {
      var sel = $(d.id);
      if (!sel) return;
      var seen = [];
      evidence.forEach(function (e) {
        var v = e[d.key];
        if (v && seen.indexOf(v) === -1) seen.push(v);
      });
      sel.innerHTML = '<option value="all">' + d.all + '</option>' +
        seen.map(function (v) {
          return '<option value="' + esc(v) + '">' + esc(v) + '</option>';
        }).join('');
    });
  }

  /* ===== 证据卡片 ===== */
  function renderCards(evidence, oppById) {
    var el = $('evidence-list');
    if (!el) return;
    el.innerHTML = evidence.map(function (e) {
      var typeCls = TYPE_CLASS[e.evidence_type] || 'type-industry';
      var credCls = CRED_CLASS[e.credibility] || 'cred-medium';
      var badges = '<span class="evidence-badge ' + typeCls + '">' + esc(e.evidence_type) + '</span>' +
        '<span class="evidence-badge ' + credCls + '">可信度 ' + esc(e.credibility) + '</span>' +
        (e.in_product_pool ? '<span class="evidence-badge in-pool">已入池</span>' : '');

      var sourceRow = '<span>📰 ' + esc(e.source) + '</span>' +
        '<span>📅 ' + esc(e.date) + '</span>' +
        '<span>🏭 ' + esc(e.industry) + '</span>' +
        (e.source_url ? '<a href="' + esc(e.source_url) + '" target="_blank" rel="noopener">查看原文 →</a>' : '');

      var sections = '';
      if (e.abstract) {
        sections += '<div class="evidence-section">' +
          '<div class="evidence-section-title">摘要</div>' +
          '<div class="evidence-section-text secondary">' + esc(e.abstract) + '</div></div>';
      }
      if (e.key_evidence) {
        sections += '<div class="evidence-section">' +
          '<div class="evidence-section-title">关键证据</div>' +
          '<div class="evidence-section-text">' + esc(e.key_evidence) + '</div></div>';
      }
      if (e.agent_explanation) {
        sections += '<div class="evidence-agent-box">' +
          '<div class="evidence-section-title">🤖 Agent 解释</div>' +
          '<div class="evidence-section-text">' + esc(e.agent_explanation) + '</div></div>';
      }
      if (e.opportunity_ids && e.opportunity_ids.length) {
        var tags = e.opportunity_ids.map(function (oid) {
          var opp = oppById[oid];
          var label = opp ? oid + ' ' + opp.title : oid;
          return '<a href="opportunities.html#' + esc(oid) + '" class="evidence-related-tag">' + esc(label) + '</a>';
        }).join('');
        sections += '<div class="evidence-section">' +
          '<div class="evidence-section-title">关联机会</div>' +
          '<div class="evidence-related">' + tags + '</div></div>';
      }

      return '<div class="evidence-card" data-industry="' + esc(e.industry) + '" data-type="' + esc(e.evidence_type) + '" data-credibility="' + esc(e.credibility) + '">' +
        '<div class="evidence-header">' +
        '<span class="evidence-id">' + esc(e.evidence_id) + '</span>' +
        '<div class="evidence-badges">' + badges + '</div>' +
        '</div>' +
        '<div class="evidence-title">' + esc(e.title) + '</div>' +
        '<div class="evidence-source-row">' + sourceRow + '</div>' +
        sections +
        '</div>';
    }).join('');
  }

  /* ===== 筛选逻辑:显隐模式作用于渲染后的卡片 ===== */
  function applyFilters() {
    var list = $('evidence-list');
    var count = $('filter-count');
    if (!list) return;
    var industry = $('filter-industry').value;
    var type = $('filter-type').value;
    var cred = $('filter-credibility').value;
    var cards = list.querySelectorAll('.evidence-card');
    var visible = 0;
    cards.forEach(function (card) {
      var match = (industry === 'all' || card.dataset.industry === industry) &&
        (type === 'all' || card.dataset.type === type) &&
        (cred === 'all' || card.dataset.credibility === cred);
      card.style.display = match ? '' : 'none';
      if (match) visible++;
    });
    if (count) count.textContent = '显示 ' + visible + ' / ' + cards.length + ' 条';
  }

  function bindFilters() {
    ['filter-industry', 'filter-type', 'filter-credibility'].forEach(function (id) {
      var sel = $(id);
      if (sel) sel.addEventListener('change', applyFilters);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var keys = Object.keys(DATA);
    Promise.all(keys.map(function (k) { return loadJson(DATA[k]); }))
      .then(function (results) {
        var d = {};
        keys.forEach(function (k, i) { d[k] = results[i]; });
        var oppById = {};
        d.opportunities.forEach(function (o) { oppById[o.opportunity_id] = o; });
        renderMeta(d.report, d.evidence.length);
        renderFilterOptions(d.evidence);
        renderCards(d.evidence, oppById);
        bindFilters();
        applyFilters();
      })
      .catch(function (err) {
        console.error('[CarbSeek Insight] 数据加载失败:', err);
        fail('evidence-list');
      });
  });
})();
