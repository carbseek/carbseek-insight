/**
 * CarbSeek Insight - 行业情报页渲染器
 * 供 industry-chemical / industry-electronics / industry-automotive / industry-eu-export 四页共用,
 * 通过 <body data-industry="..."> 区分行业,从 data/*.json 加载数据渲染,JSON 为唯一真相源。
 * 无依赖,原生 ES6,GitHub Pages 纯静态可用。
 */
(function () {
  'use strict';

  var DATA = {
    evidence: 'data/evidence/evidence_pool.json',
    opportunities: 'data/opportunities/opportunity_pool.json',
    trends: 'data/industries/trends.json',
    recommendations: 'data/industries/recommendations.json',
    report: 'data/reports/WR-2026-W30.json'
  };

  /* 页面文案配置(非情报数据):hero 图标 / 标题 / 一句话定位 */
  var INDUSTRY_CONFIG = {
    '化工': {
      icon: '🔬',
      title: '化工行业情报',
      tagline: '聚焦化工行业碳足迹、碳标签、Scope 3 排放因子与供应链碳管理动态'
    },
    '电子电气': {
      icon: '💻',
      title: '电子电气行业情报',
      tagline: '聚焦电子电气产品碳标签、韩国强制碳标签、中欧互认与供应链碳管理'
    },
    '汽车': {
      icon: '🚗',
      title: '汽车行业情报',
      tagline: '聚焦汽车 EPD、电池法规碳足迹声明、iNEDC/WLTP 数据对接与整车碳核算'
    },
    '欧盟出口': {
      icon: '🇪🇺',
      title: '欧盟出口行业情报',
      tagline: '聚焦 CBAM、电池法规、REACH 与欧盟碳合规工具需求'
    }
  };

  /* evidence_type -> 标签样式/文案 */
  var TAG_CLASS = {
    '政策': 'policy',
    '学术': 'academic',
    '专利': 'patent',
    '竞品': 'competitor',
    '行业应用': 'competitor'
  };
  var TAG_LABEL = { '行业应用': '行业' };

  /* 行动建议图标 */
  var REC_ICON = { field: '📊', template: '📋', plugin: '🔌' };

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

  function emptyNote() {
    return '<div style="padding:14px 0;font-size:12px;color:var(--text-secondary);">本周暂无收录</div>';
  }

  /* ===== 报头:WR 编号 ===== */
  function renderMeta(report) {
    var el = $('report-id');
    if (el) el.textContent = report.report_id;
  }

  /* ===== Hero:图标/标题/定位 + 三项统计 ===== */
  function renderHero(industry, evidence, opportunities, trends) {
    var cfg = INDUSTRY_CONFIG[industry];
    if (!cfg) return;
    if ($('hero-title')) $('hero-title').textContent = cfg.icon + ' ' + cfg.title;
    if ($('hero-tagline')) $('hero-tagline').textContent = cfg.tagline;

    var evCount = evidence.filter(function (e) { return e.industry === industry; }).length;
    var opCount = opportunities.filter(function (o) { return o.industry === industry; }).length;
    var trend = trends[industry] || {};
    if ($('stat-evidence')) $('stat-evidence').textContent = evCount;
    if ($('stat-opps')) $('stat-opps').textContent = opCount;
    if ($('stat-score')) $('stat-score').textContent = trend.score != null ? trend.score : '-';
  }

  /* ===== 证据条目(政策/论文/企业动作三个区块共用) ===== */
  function renderEvidenceBlock(id, items) {
    var el = $(id);
    if (!el) return;
    if (!items.length) { el.innerHTML = emptyNote(); return; }
    el.innerHTML = items.map(function (e) {
      var cls = TAG_CLASS[e.evidence_type] || 'competitor';
      var label = TAG_LABEL[e.evidence_type] || e.evidence_type;
      return '<div class="evidence-item">' +
        '<div class="evidence-title">' + esc(e.title) + '</div>' +
        '<div class="evidence-meta">' +
        '<span class="evidence-tag ' + cls + '">' + esc(label) + '</span>' +
        '<span>' + esc(e.date) + '</span>' +
        '<span>' + esc(e.source) + '</span>' +
        '</div>' +
        '<div class="evidence-abstract">' + esc(e.abstract) + '</div>' +
        '</div>';
    }).join('');
  }

  function byDateDesc(a, b) { return a.date < b.date ? 1 : (a.date > b.date ? -1 : 0); }

  function renderEvidenceSections(industry, evidence) {
    var own = evidence.filter(function (e) { return e.industry === industry; }).sort(byDateDesc);
    renderEvidenceBlock('policy-list', own.filter(function (e) { return e.evidence_type === '政策'; }));
    renderEvidenceBlock('academic-list', own.filter(function (e) { return e.evidence_type === '学术'; }));
    renderEvidenceBlock('company-list', own.filter(function (e) {
      return e.evidence_type === '竞品' || e.evidence_type === '行业应用';
    }));
  }

  /* ===== CarbSeek 产品机会 ===== */
  function renderOpportunities(industry, opportunities) {
    var el = $('opp-list');
    if (!el) return;
    var items = opportunities.filter(function (o) { return o.industry === industry; });
    if (!items.length) { el.innerHTML = emptyNote(); return; }
    el.innerHTML = items.map(function (o) {
      var color = o.status === '已立项' ? 'var(--accent-green)' : 'var(--accent-red)';
      return '<div class="opp-card">' +
        '<div class="opp-card-title">' + esc(o.title) + '</div>' +
        '<div class="opp-card-meta">' +
        '<span style="color: ' + color + ';">●</span> ' + esc(o.status) +
        '<span>商业 ' + esc(o.business_value) + ' | 技术 ' + esc(o.tech_feasibility) + ' | 证据 ' + esc(o.evidence_grade) + '</span>' +
        '</div></div>';
    }).join('');
  }

  /* ===== 行动建议(field/template/plugin 三组) ===== */
  function renderRecommendations(industry, recommendations) {
    var list = recommendations[industry] || [];
    ['field', 'template', 'plugin'].forEach(function (type) {
      var el = $('rec-' + type);
      if (!el) return;
      var items = list.filter(function (r) { return r.type === type; });
      if (!items.length) { el.innerHTML = emptyNote(); return; }
      el.innerHTML = items.map(function (r) {
        return '<div class="rec-item">' +
          '<div class="rec-icon ' + esc(type) + '">' + (REC_ICON[type] || '📌') + '</div>' +
          '<div class="rec-text"><strong>' + esc(r.name) + '</strong>：' + esc(r.desc) + '</div>' +
          '</div>';
      }).join('');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var industry = document.body.getAttribute('data-industry');
    if (!industry || !INDUSTRY_CONFIG[industry]) {
      console.error('[CarbSeek Insight] 未知行业:', industry);
      return;
    }
    var keys = Object.keys(DATA);
    Promise.all(keys.map(function (k) { return loadJson(DATA[k]); }))
      .then(function (results) {
        var d = {};
        keys.forEach(function (k, i) { d[k] = results[i]; });
        renderMeta(d.report);
        renderHero(industry, d.evidence, d.opportunities, d.trends);
        renderEvidenceSections(industry, d.evidence);
        renderOpportunities(industry, d.opportunities);
        renderRecommendations(industry, d.recommendations);
      })
      .catch(function (err) {
        console.error('[CarbSeek Insight] 数据加载失败:', err);
        ['policy-list', 'academic-list', 'company-list', 'opp-list',
          'rec-field', 'rec-template', 'rec-plugin'].forEach(fail);
      });
  });
})();
