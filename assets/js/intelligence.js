/**
 * CarbSeek Insight - 情报中心渲染器
 * 从 data/*.json 加载数据并渲染各区块,JSON 为唯一真相源。
 * 无依赖,原生 ES6,GitHub Pages 纯静态可用。
 */
(function () {
  'use strict';

  var DATA = {
    articles: 'data/intelligence/articles.json',
    countdown: 'data/policy_countdown.json',
    report: 'data/reports/WR-2026-W30.json'
  };

  var TYPE_LABEL = { news: '资讯', academic: '学术', patent: '专利', policy: '政策', industry: '行业' };
  var TYPE_ORDER = ['news', 'industry', 'policy', 'academic', 'patent'];
  var TYPE_COLOR = {
    news: '#3b82f6', industry: '#10b981', policy: '#ef4444',
    academic: '#8b5cf6', patent: '#06b6d4'
  };
  var INDUSTRY_ORDER = ['通用', '电子电气', '化工', '汽车', '欧盟出口'];
  var INDUSTRY_BAR_COLOR = '#8b5cf6';
  var HIGH_VALUE_THRESHOLD = 0.6;

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

  function parseDate(d) { return new Date(d + 'T00:00:00'); }

  function scoreColor(score) {
    if (score > 0.8) return '#ef4444';
    if (score >= 0.6) return '#f59e0b';
    return '#3b82f6';
  }

  /* ===== 报头:版本 + WR 编号 + 截止日期 ===== */
  function renderMeta(report) {
    var el = $('report-meta');
    if (!el) return;
    el.textContent = '情报中心 v2.0 | ' + report.report_id + ' | 截至 ' + (report.week_ending || '');
  }

  /* ===== 统计 5 卡 ===== */
  function renderStats(articles, countdown) {
    var latest = articles.reduce(function (max, a) {
      return a.publish_date > max ? a.publish_date : max;
    }, '');
    var latestTs = parseDate(latest).getTime();
    var today = articles.filter(function (a) { return a.publish_date === latest; }).length;
    var week = articles.filter(function (a) {
      var diff = (latestTs - parseDate(a.publish_date).getTime()) / 86400000;
      return diff >= 0 && diff <= 7;
    }).length;
    var high = articles.filter(function (a) { return a.relevance_score >= HIGH_VALUE_THRESHOLD; }).length;
    var urgent = countdown.filter(function (p) { return p.urgency === 'critical'; }).length;

    if ($('stat-total')) $('stat-total').textContent = articles.length;
    if ($('stat-today')) $('stat-today').textContent = today;
    if ($('stat-week')) $('stat-week').textContent = week;
    if ($('stat-high')) $('stat-high').textContent = high;
    if ($('stat-urgent')) $('stat-urgent').textContent = urgent;
  }

  /* ===== 一句话判断 ===== */
  function renderJudgment(report) {
    var el = $('judgment-text');
    if (el) el.textContent = report.one_sentence_judgment;
  }

  /* ===== 情报流(按相关度排序,Tab 真实筛选) ===== */
  function renderArticles(articles) {
    var el = $('article-list');
    if (!el) return;
    var sorted = articles.map(function (a, i) { return { a: a, i: i }; })
      .sort(function (x, y) {
        return (y.a.relevance_score - x.a.relevance_score) || (x.i - y.i);
      });
    el.innerHTML = sorted.map(function (w) {
      var a = w.a;
      var type = a.source_type || 'news';
      var pct = Math.round(a.relevance_score * 100);
      var title = a.url
        ? '<a href="' + esc(a.url) + '" class="page-link" target="_blank" rel="noopener">' + esc(a.title) + '</a>'
        : esc(a.title);
      return '<div class="article-item" data-type="' + esc(type) + '">' +
        '<span class="article-badge badge-' + esc(type) + '">' + esc(TYPE_LABEL[type] || type) + '</span>' +
        '<div class="article-content">' +
        '<div class="article-title">' + title + '</div>' +
        '<div class="article-summary">' + esc(a.summary) + '</div>' +
        '<div class="article-meta">' +
        '<span>' + esc(a.source) + '</span>' +
        '<span>' + esc(a.industry) + '</span>' +
        '<span>' + esc(a.publish_date) + '</span>' +
        '<span>相关度: ' + esc(a.relevance_score.toFixed(2)) +
        '<span class="score-bar"><span class="score-fill" style="width:' + pct + '%;background:' + scoreColor(a.relevance_score) + '"></span></span></span>' +
        '</div></div></div>';
    }).join('');
  }

  function bindTabs() {
    var tabs = $('article-tabs');
    if (!tabs) return;
    tabs.querySelectorAll('.tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        var type = tab.getAttribute('data-type');
        document.querySelectorAll('#article-list .article-item').forEach(function (item) {
          item.style.display = (type === 'all' || item.getAttribute('data-type') === type) ? '' : 'none';
        });
      });
    });
  }

  /* ===== 政策倒计时(天数按 deadline 实时计算) ===== */
  function renderCountdown(items) {
    var el = $('countdown-list');
    if (!el) return;
    var sorted = items.slice().sort(function (a, b) {
      return a.deadline < b.deadline ? -1 : (a.deadline > b.deadline ? 1 : 0);
    });
    el.innerHTML = sorted.map(function (it) {
      var urg = it.urgency === 'critical' ? 'critical' : 'high';
      return '<div class="countdown-item">' +
        '<div class="countdown-days days-' + urg + '">' +
        '<span class="days-num">' + daysUntil(it.deadline) + '</span>' +
        '<span class="days-label">天</span>' +
        '</div>' +
        '<div class="countdown-info">' +
        '<div class="countdown-title">' + esc(it.policy) + '</div>' +
        '<div class="countdown-deadline">' + esc(it.issuing_body) + ' | 截止: ' + esc(it.deadline) + '</div>' +
        '</div></div>';
    }).join('');
  }

  /* ===== 情报来源分布(按 source_type 聚合,宽度 = 占比) ===== */
  function renderSourceDist(articles) {
    var el = $('source-dist');
    if (!el) return;
    var counts = {};
    articles.forEach(function (a) {
      var t = a.source_type || 'news';
      counts[t] = (counts[t] || 0) + 1;
    });
    var rows = TYPE_ORDER.filter(function (t) { return counts[t]; })
      .map(function (t) { return { type: t, count: counts[t] }; })
      .sort(function (a, b) { return b.count - a.count; });
    var total = articles.length || 1;
    el.innerHTML = rows.map(function (r) {
      var pct = (r.count / total * 100).toFixed(1);
      return '<div class="source-bar">' +
        '<span class="source-name">' + esc(TYPE_LABEL[r.type] || r.type) + '</span>' +
        '<div class="source-track"><div class="source-fill" style="width:' + pct + '%;background:' + (TYPE_COLOR[r.type] || '#3b82f6') + '"></div></div>' +
        '<span class="source-count">' + r.count + '</span>' +
        '</div>';
    }).join('');
  }

  /* ===== 行业覆盖(按 industry 聚合,宽度相对最大值) ===== */
  function renderIndustryDist(articles) {
    var el = $('industry-dist');
    if (!el) return;
    var counts = {};
    articles.forEach(function (a) {
      var ind = a.industry || '通用';
      counts[ind] = (counts[ind] || 0) + 1;
    });
    var names = INDUSTRY_ORDER.filter(function (n) { return counts[n]; });
    Object.keys(counts).forEach(function (n) {
      if (names.indexOf(n) === -1) names.push(n);
    });
    var rows = names.map(function (n) { return { name: n, count: counts[n] }; })
      .sort(function (a, b) { return b.count - a.count; });
    var max = rows.reduce(function (m, r) { return Math.max(m, r.count); }, 1);
    el.innerHTML = rows.map(function (r) {
      var pct = (r.count / max * 100).toFixed(1);
      return '<div class="source-bar">' +
        '<span class="source-name">' + esc(r.name) + '</span>' +
        '<div class="source-track"><div class="source-fill" style="width:' + pct + '%;background:' + INDUSTRY_BAR_COLOR + '"></div></div>' +
        '<span class="source-count">' + r.count + '</span>' +
        '</div>';
    }).join('');
  }

  /* ===== 研发建议(文本含【P0】前缀,解析参照 dashboard.js) ===== */
  function renderRdSuggestions(list) {
    var el = $('rd-list');
    if (!el) return;
    el.innerHTML = list.map(function (s) {
      var m = s.match(/^【(P\d)】(.*)$/);
      var prio = m ? m[1] : 'P2';
      var text = m ? m[2] : s;
      return '<div class="rd-item">' +
        '<span class="rd-priority ' + prio.toLowerCase() + '">' + prio + '</span>' +
        '<div>' + esc(text) + '</div>' +
        '</div>';
    }).join('');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var keys = Object.keys(DATA);
    Promise.all(keys.map(function (k) { return loadJson(DATA[k]); }))
      .then(function (results) {
        var d = {};
        keys.forEach(function (k, i) { d[k] = results[i]; });
        renderMeta(d.report);
        renderStats(d.articles, d.countdown);
        renderJudgment(d.report);
        renderArticles(d.articles);
        bindTabs();
        renderCountdown(d.countdown);
        renderSourceDist(d.articles);
        renderIndustryDist(d.articles);
        renderRdSuggestions(d.report.rd_suggestions);
      })
      .catch(function (err) {
        console.error('[CarbSeek Intelligence] 数据加载失败:', err);
        ['judgment-text', 'article-list', 'countdown-list', 'source-dist',
          'industry-dist', 'rd-list'].forEach(fail);
      });
  });
})();
