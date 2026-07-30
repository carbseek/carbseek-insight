/**
 * CarbSeek Insight - 首页渲染器
 * 从 data/*.json 加载数据并渲染各区块,JSON 为唯一真相源。
 * 无依赖,原生 ES6,GitHub Pages 纯静态可用。
 */
(function () {
  'use strict';

  var DATA = {
    report: 'data/reports/WR-2026-W30.json',
    radar: 'data/radar/this_week.json',
    countdown: 'data/policy_countdown.json',
    trends: 'data/industries/trends.json',
    opportunities: 'data/opportunities/opportunity_pool.json',
    intelCenter: 'data/intel_center.json',
    competitors: 'data/competitors.json'
  };

  var SEVERITY_LABEL = { critical: 'CRITICAL', high: 'HIGH', medium: 'MEDIUM', low: 'LOW' };
  var INDUSTRY_DOT = {
    '欧盟出口': 'var(--accent-amber)',
    '化工': 'var(--accent-blue)',
    '电子电气': 'var(--accent-purple)',
    '汽车': 'var(--accent-cyan)',
    '通用': 'var(--text-secondary)'
  };
  var TREND_STYLE = {
    '化工': { icon: '🔬', cls: 'chemical' },
    '电子电气': { icon: '💻', cls: 'electronics' },
    '汽车': { icon: '🚗', cls: 'automotive' },
    '欧盟出口': { icon: '🇪🇺', cls: 'eu-export' }
  };
  var STAT_COLOR = {
    blue: 'var(--accent-blue)', green: 'var(--accent-green)',
    purple: 'var(--accent-purple)', amber: 'var(--accent-amber)'
  };

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

  function daysUntil(deadline) {
    var now = new Date(); now.setHours(0, 0, 0, 0);
    var end = new Date(deadline + 'T00:00:00');
    return Math.max(0, Math.round((end - now) / 86400000));
  }

  /* ===== 报头:WR 编号 + 截止日期 ===== */
  function renderMeta(report) {
    var el = $('report-meta');
    if (!el) return;
    var d = report.week_ending || '';
    el.textContent = report.report_id + ' | 截至 ' + d.replace(/-/g, '.');
  }

  /* ===== 一句话判断 ===== */
  function renderJudgment(report) {
    var el = $('judgment-text');
    if (el) el.textContent = report.one_sentence_judgment;
  }

  /* ===== 本周重大变化 Top 5 ===== */
  function renderRadar(items) {
    var el = $('radar-list');
    if (!el) return;
    el.innerHTML = items.slice(0, 5).map(function (it, i) {
      var sev = (it.severity || 'medium').toLowerCase();
      return '<div class="radar-item">' +
        '<div class="radar-number">' + (i + 1) + '</div>' +
        '<div class="radar-content">' +
        '<div class="radar-title">' + esc(it.title) + '</div>' +
        '<div class="radar-meta">' +
        '<span class="severity severity-' + sev + '">' + (SEVERITY_LABEL[sev] || sev.toUpperCase()) + '</span>' +
        '<span class="radar-tag">' + esc(it.category) + '</span>' +
        '<span>' + esc(it.industry) + '</span>' +
        '<span>' + esc(it.date) + '</span>' +
        '</div></div></div>';
    }).join('');
  }

  /* ===== 政策倒计时(天数按 deadline 实时计算) ===== */
  function renderCountdown(items) {
    var el = $('countdown-list');
    if (!el) return;
    el.innerHTML = items.map(function (it) {
      var urg = it.urgency === 'critical' ? 'critical' : 'high';
      return '<div class="countdown-item">' +
        '<div class="countdown-days ' + urg + '">' +
        '<span class="days-num">' + daysUntil(it.deadline) + '</span>' +
        '<span class="days-label">天</span>' +
        '</div>' +
        '<div class="countdown-info">' +
        '<div class="countdown-title">' + esc(it.policy) + '</div>' +
        '<div class="countdown-deadline">Deadline: ' + esc(it.deadline) + '</div>' +
        '</div></div>';
    }).join('');
  }

  /* ===== 情报中心:Agent 状态 / 统计 / 最新情报 ===== */
  function renderIntelCenter(ic) {
    var agents = $('agent-status');
    if (agents) {
      agents.innerHTML = ic.agents.map(function (a, i) {
        var border = i < ic.agents.length - 1 ? 'border-bottom: 1px solid var(--border-color);' : '';
        return '<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; ' + border + '">' +
          '<span style="font-size: 12px;">' + esc(a.icon) + ' ' + esc(a.name) + '</span>' +
          '<span style="font-size: 11px; color: var(--accent-green);">' + esc(a.status) + '</span>' +
          '</div>';
      }).join('');
    }
    var stats = $('intel-stats');
    if (stats) {
      stats.innerHTML = ic.stats.map(function (s) {
        return '<div style="padding: 12px; background: var(--bg-secondary); border-radius: 8px;">' +
          '<div style="font-size: 24px; font-weight: 700; color: ' + (STAT_COLOR[s.color] || 'var(--accent-blue)') + ';">' + esc(s.value) + '</div>' +
          '<div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">' + esc(s.label) + '</div>' +
          '</div>';
      }).join('');
    }
    var freq = $('intel-freq');
    if (freq) freq.textContent = '更新频率: ' + ic.update_frequency;
    var latest = $('latest-intel');
    if (latest) {
      latest.innerHTML = ic.latest.map(function (it, i) {
        var border = i < ic.latest.length - 1 ? '' : ' border-bottom: none;';
        return '<div class="radar-item" style="padding: 10px 16px;' + border + '">' +
          '<div class="radar-content">' +
          '<div class="radar-title" style="font-size: 12px;">' + esc(it.title) + '</div>' +
          '<div class="radar-meta">' +
          '<span class="radar-tag">' + esc(it.tag) + '</span>' +
          '<span>' + esc(it.meta) + '</span>' +
          '</div></div></div>';
      }).join('');
    }
  }

  /* ===== 行业热度趋势 ===== */
  function renderTrends(trends) {
    var el = $('trend-grid');
    if (!el) return;
    el.innerHTML = Object.keys(TREND_STYLE).map(function (name) {
      var t = trends[name];
      if (!t) return '';
      var st = TREND_STYLE[name];
      return '<div class="card"><div class="card-body"><div class="trend-bar">' +
        '<div class="trend-header">' +
        '<span class="trend-name">' + st.icon + ' ' + esc(name) + '</span>' +
        '<span><span class="trend-score">' + esc(t.score) + '</span>' +
        '<span class="trend-change up">↑' + esc(t.change) + '</span></span>' +
        '</div>' +
        '<div class="trend-track"><div class="trend-fill ' + st.cls + '" style="width: ' + esc(t.score) + '%;"></div></div>' +
        '<div class="trend-theme">热点:' + esc(t.top_theme) + '</div>' +
        '</div></div></div>';
    }).join('');
  }

  /* ===== 本周产品机会 Top 10(顺序由周报的 top_opportunities 决定) ===== */
  function renderOpportunities(pool, order) {
    var el = $('opp-list');
    if (!el) return;
    var byId = {};
    pool.forEach(function (o) { byId[o.opportunity_id] = o; });
    el.innerHTML = order.map(function (id, i) {
      var o = byId[id];
      if (!o) return '';
      var rankCls = i < 3 ? 'p0' : (i < 8 ? 'p1' : 'p2');
      var done = o.status === '已立项';
      return '<div class="opp-item">' +
        '<div class="opp-rank ' + rankCls + '">' + (i + 1) + '</div>' +
        '<div class="opp-content">' +
        '<div class="opp-title">' + esc(o.title) + '</div>' +
        '<div class="opp-meta">' +
        '<span style="color: ' + (INDUSTRY_DOT[o.industry] || 'var(--text-secondary)') + ';">●</span> ' + esc(o.industry) +
        '<span class="opp-score">' +
        '<span class="score-pill biz">商业 ' + esc(o.business_value) + '</span>' +
        '<span class="score-pill tech">技术 ' + esc(o.tech_feasibility) + '</span>' +
        '<span class="score-pill grade-a">证据 ' + esc(o.evidence_grade) + '</span>' +
        '</span>' +
        '<span>' + esc(o.source_count) + ' 条证据</span>' +
        '<span style="color: ' + (done ? 'var(--accent-green)' : 'var(--accent-red)') + ';">' + esc(o.status) + '</span>' +
        '</div></div></div>';
    }).join('');
  }

  /* ===== 竞品动态 ===== */
  function renderCompetitors(data) {
    var el = $('comp-list');
    if (!el) return;
    el.innerHTML = data.competitors.map(function (c) {
      return '<div class="comp-item">' +
        '<div class="comp-avatar">' + esc(c.avatar) + '</div>' +
        '<div class="comp-content">' +
        '<div class="comp-name">' + esc(c.name) + '</div>' +
        '<div class="comp-action">' + esc(c.action) + '</div>' +
        '<div class="comp-impact">' + esc(c.impact) + '</div>' +
        '</div></div>';
    }).join('');
  }

  /* ===== 下周研发建议(文本含【P0】前缀) ===== */
  function renderRdSuggestions(list) {
    var el = $('rd-list');
    if (!el) return;
    el.innerHTML = list.map(function (s) {
      var m = s.match(/^【(P\d)】(.*)$/);
      var prio = m ? m[1] : 'P2';
      var text = m ? m[2] : s;
      return '<div class="rd-item">' +
        '<span class="rd-priority ' + prio.toLowerCase() + '">' + prio + '</span>' +
        '<div class="rd-text">' + esc(text) + '</div>' +
        '</div>';
    }).join('');
  }

  /* ===== 产品影响分析 ===== */
  function renderImpacts(report) {
    if ($('impact-pro')) $('impact-pro').textContent = report.impact_pro;
    if ($('impact-scan')) $('impact-scan').textContent = report.impact_scan;
    if ($('impact-db')) $('impact-db').textContent = report.impact_db;
  }

  /* ===== 演示数据徽标 ===== */
  function renderDemoBadge(sources) {
    var isDemo = sources.some(function (s) { return s && s.demo === true; });
    var el = $('demo-badge');
    if (el && isDemo) {
      el.innerHTML = ' <span class="badge" style="background: rgba(245,158,11,0.15); color: var(--accent-amber);">演示数据</span>';
    }
  }

  /* ===== 进度条动画(渲染完成后触发) ===== */
  function animateTrends() {
    document.querySelectorAll('.trend-fill').forEach(function (fill) {
      var width = fill.style.width;
      fill.style.width = '0%';
      setTimeout(function () { fill.style.width = width; }, 300);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var keys = Object.keys(DATA);
    Promise.all(keys.map(function (k) { return loadJson(DATA[k]); }))
      .then(function (results) {
        var d = {};
        keys.forEach(function (k, i) { d[k] = results[i]; });
        renderMeta(d.report);
        renderJudgment(d.report);
        renderRadar(d.radar);
        renderCountdown(d.countdown);
        renderIntelCenter(d.intelCenter);
        renderTrends(d.trends);
        renderOpportunities(d.opportunities, d.report.top_opportunities);
        renderCompetitors(d.competitors);
        renderRdSuggestions(d.report.rd_suggestions);
        renderImpacts(d.report);
        renderDemoBadge([d.report, d.intelCenter, d.competitors]);
        animateTrends();
      })
      .catch(function (err) {
        console.error('[CarbSeek Insight] 数据加载失败:', err);
        ['radar-list', 'countdown-list', 'agent-status', 'intel-stats', 'latest-intel',
          'trend-grid', 'opp-list', 'comp-list', 'rd-list'].forEach(fail);
      });
  });
})();
