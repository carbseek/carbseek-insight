import { useEffect, useState } from 'react';
import { api, getToken, clearToken, setUnauthorizedHandler } from './api.js';
import { ENTITIES, ENTITY_TABS } from './entities.js';
import Login from './components/Login.jsx';
import Overview from './components/Overview.jsx';
import EntityPage from './components/EntityPage.jsx';
import ReportsPage from './components/ReportsPage.jsx';
import IntelCenterPage from './components/IntelCenterPage.jsx';
import Modal from './components/Modal.jsx';

// exportAll() summary keys → the data/*.json file each one writes
const EXPORT_FILES = {
  evidence: 'data/evidence/evidence_pool.json',
  opportunities: 'data/opportunities/opportunity_pool.json',
  radar_items: 'data/radar/this_week.json',
  policies: 'data/policy_countdown.json',
  articles: 'data/intelligence/articles.json',
  competitors: 'data/competitors.json',
  trends: 'data/industries/trends.json',
  recommendations: 'data/industries/recommendations.json',
  reports: 'data/reports/*.json',
  intel_center: 'data/intel_center.json',
};

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());
  const [tab, setTab] = useState('overview');
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null); // {summary} | {error}

  useEffect(() => {
    setUnauthorizedHandler(() => setAuthed(false));
    return () => setUnauthorizedHandler(null);
  }, []);

  if (!authed) return <Login onLogin={() => setAuthed(true)} />;

  const logout = () => {
    clearToken();
    setAuthed(false);
  };

  const doExport = async () => {
    setExporting(true);
    try {
      const data = await api('/api/admin/export', { method: 'POST' });
      setExportResult({ summary: data.summary });
    } catch (e) {
      setExportResult({ error: e.message });
    } finally {
      setExporting(false);
    }
  };

  const renderPage = () => {
    if (tab === 'overview') return <Overview />;
    if (tab === 'reports') return <ReportsPage />;
    if (tab === 'intel_center') return <IntelCenterPage />;
    return <EntityPage key={tab} config={ENTITIES[tab]} />;
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-row">
          <span className="brand">CarbSeek Insight <span className="brand-sub">管理后台</span></span>
          <div className="topbar-actions">
            <button className="btn btn-accent" onClick={doExport} disabled={exporting}>
              {exporting ? '导出中…' : '导出并发布'}
            </button>
            <button className="btn" onClick={logout}>退出登录</button>
          </div>
        </div>
        <nav className="tabs">
          <button className={tab === 'overview' ? 'tab active' : 'tab'} onClick={() => setTab('overview')}>概览</button>
          {ENTITY_TABS.map((key) => (
            <button key={key} className={tab === key ? 'tab active' : 'tab'} onClick={() => setTab(key)}>
              {ENTITIES[key].label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main">{renderPage()}</main>

      {exportResult && (
        <Modal title="导出结果" onClose={() => setExportResult(null)}>
          {exportResult.error ? (
            <div className="banner banner-err">{exportResult.error}</div>
          ) : (
            <>
              <p>已将 SQLite 数据导出回 data/*.json:</p>
              <table className="data-table">
                <thead><tr><th>文件</th><th>条数</th></tr></thead>
                <tbody>
                  {Object.entries(exportResult.summary ?? {}).map(([key, count]) => (
                    <tr key={key}><td className="mono">{EXPORT_FILES[key] ?? key}</td><td>{String(count)}</td></tr>
                  ))}
                </tbody>
              </table>
              <p className="muted">提示:本阶段仅导出到本地 data/ 目录,git 发布将在下一阶段接入。</p>
            </>
          )}
          <div className="form-actions">
            <button className="btn btn-primary" onClick={() => setExportResult(null)}>关闭</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
