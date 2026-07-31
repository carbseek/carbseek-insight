/**
 * CarbSeek Insight - 机会库渲染器
 * 从 data/*.json 加载机会池并渲染统计、卡片与优先级 Tab,JSON 为唯一真相源。
 * 无依赖,原生 ES6,GitHub Pages 纯静态可用。
 */
(function () {
  'use strict';

  var DATA = {
    opportunities: 'data/opportunities/opportunity_pool.json',
    report: 'data/reports/WR-2026-W30.json'
  };

  var INDUSTRY_ICON = {
    '化工': '🔬',
    '电子电气': '💻',
    '汽车': '🚗',
    '欧盟出口': '🇪🇺',
    '通用': '●'
  };
  var STATUS_CLASS = {
    '待评审': 'status-pending',
    '已立项': 'status-approved',
    '已完成': 'status-done'
  };
  var GRADE_CLASS = { 'A': 'grade-a', 'B': 'grade-b', 'C': 'grade-c' };
  var REVENUE_CLASS = { '高': 'high', '中': 'medium', '低': 'low' };
  var PRIORITY_ORDER = { 'P0': 0, 'P1': 1, 'P2': 2 };

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

  /* 分数颜色分级:>=8 高,6-7 中,<=5 低 */
  function scoreClass(n) {
    n = Number(n);
    return n >= 8 ? 'high' : (n >= 6 ? 'medium' : 'low');
  }

  /* ===== 报头:WR 编号 + 机会总数 ===== */
  function renderMeta(report, total) {
    var meta = $('report-meta');
    if (meta) meta.textContent = report.report_id;
    var el = $('opp-total');
    if (el) el.textContent = '共 ' + total + ' 个机会';
  }

  /* ===== 统计条:按 priority 聚合 ===== */
  function renderStats(opportunities) {
    var el = $('stats-bar');
    if (!el) return;
    var counts = { P0: 0, P1: 0, P2: 0 };
    opportunities.forEach(function (o) {
      if (counts[o.priority] != null) counts[o.priority]++;
    });
    var cells = [
      { cls: 'p0', value: counts.P0, label: 'P0 紧急机会' },
      { cls: 'p1', value: counts.P1, label: 'P1 重要机会' },
      { cls: 'p2', value: counts.P2, label: 'P2 观察机会' },
      { cls: 'total', value: opportunities.length, label: '总计' }
    ];
    el.innerHTML = cells.map(function (c) {
      return '<div class="stat-card">' +
        '<div class="stat-value ' + c.cls + '">' + c.value + '</div>' +
        '<div class="stat-label">' + c.label + '</div>' +
        '</div>';
    }).join('');
  }

  /* ===== 机会卡片:排序 P0 -> P1 -> P2,同级按 opportunity_id ===== */
  function renderCards(opportunities) {
    var el = $('opp-list');
    if (!el) return;
    var sorted = opportunities.slice().sort(function (a, b) {
      var pa = PRIORITY_ORDER[a.priority] != null ? PRIORITY_ORDER[a.priority] : 9;
      var pb = PRIORITY_ORDER[b.priority] != null ? PRIORITY_ORDER[b.priority] : 9;
      if (pa !== pb) return pa - pb;
      return String(a.opportunity_id).localeCompare(String(b.opportunity_id));
    });
    el.innerHTML = sorted.map(function (o) {
      var icon = INDUSTRY_ICON[o.industry] || '●';
      var gradeCls = GRADE_CLASS[o.evidence_grade] || 'grade-c';
      var statusCls = STATUS_CLASS[o.status] || 'status-pending';
      var revenueCls = REVENUE_CLASS[o.revenue_potential] || 'medium';
      var priority = String(o.priority || '').toLowerCase();

      return '<div class="opportunity-detail" data-priority="' + esc(priority) + '" id="' + esc(o.opportunity_id) + '">' +
        '<div class="opp-header">' +
        '<span class="opp-id">' + esc(o.opportunity_id) + '</span>' +
        '<div class="opp-badges">' +
        '<span class="opp-badge industry">' + icon + ' ' + esc(o.industry) + '</span>' +
        '<span class="opp-badge ' + gradeCls + '">证据 ' + esc(o.evidence_grade) + '</span>' +
        '<span class="opp-badge ' + statusCls + '">' + esc(o.status) + '</span>' +
        '</div></div>' +
        '<div class="opp-title">' + esc(o.title) + '</div>' +
        '<div class="opp-description">' + esc(o.description) + '</div>' +
        '<div class="score-grid">' +
        '<div class="score-cell"><div class="score-label">商业价值</div>' +
        '<div class="score-value ' + scoreClass(o.business_value) + '">' + esc(o.business_value) + '</div></div>' +
        '<div class="score-cell"><div class="score-label">技术可行性</div>' +
        '<div class="score-value ' + scoreClass(o.tech_feasibility) + '">' + esc(o.tech_feasibility) + '</div></div>' +
        '<div class="score-cell"><div class="score-label">收益潜力</div>' +
        '<div class="score-value ' + revenueCls + '">' + esc(o.revenue_potential) + '</div></div>' +
        '<div class="score-cell"><div class="score-label">证据条数</div>' +
        '<div class="score-value">' + esc(o.source_count) + '</div></div>' +
        '</div>' +
        '<div class="impact-section">' +
        '<div class="impact-title">对 CarbSeek 产品影响</div>' +
        '<div class="impact-grid">' +
        '<div class="impact-cell pro"><div class="impact-cell-title pro">CarbSeek Pro</div>' +
        '<div class="impact-cell-text">' + esc(o.impact_pro) + '</div></div>' +
        '<div class="impact-cell scan"><div class="impact-cell-title scan">CarbSeek Scan</div>' +
        '<div class="impact-cell-text">' + esc(o.impact_scan) + '</div></div>' +
        '<div class="impact-cell db"><div class="impact-cell-title db">数据库建设</div>' +
        '<div class="impact-cell-text">' + esc(o.impact_db) + '</div></div>' +
        '</div></div>' +
        '<div class="opp-meta-row">' +
        '<span>👤 建议负责人：' + esc(o.suggested_owner) + '</span>' +
        '<span>📅 创建于 ' + esc(o.created_at) + '</span>' +
        '<a href="evidence.html">查看证据 →</a>' +
        '</div></div>';
    }).join('');
  }

  /* ===== 优先级 Tab 筛选 ===== */
  function bindTabs() {
    var tabs = document.querySelectorAll('.priority-tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        var filter = tab.dataset.filter;
        document.querySelectorAll('.opportunity-detail').forEach(function (opp) {
          opp.style.display = (filter === 'all' || opp.dataset.priority === filter) ? '' : 'none';
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var keys = Object.keys(DATA);
    Promise.all(keys.map(function (k) { return loadJson(DATA[k]); }))
      .then(function (results) {
        var d = {};
        keys.forEach(function (k, i) { d[k] = results[i]; });
        renderMeta(d.report, d.opportunities.length);
        renderStats(d.opportunities);
        renderCards(d.opportunities);
        bindTabs();
      })
      .catch(function (err) {
        console.error('[CarbSeek Insight] 数据加载失败:', err);
        ['stats-bar', 'opp-list'].forEach(fail);
      });
  });
})();
