import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { ENTITIES } from '../entities.js';

// Overview: per-entity counts + the latest weekly report's one-line judgment.
export default function Overview() {
  const [state, setState] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const listEntity = async (key) => {
          const cfg = ENTITIES[key];
          const data = await api(cfg.api === '/api/intel-center' ? cfg.api : cfg.api);
          if (cfg.single) return data; // object, not a list
          return cfg.listFrom ? cfg.listFrom(data) : data;
        };
        const [dashboard, evidence, opportunities, policies, articles, competitors, trends, recommendations, intel] =
          await Promise.all([
            api('/api/dashboard'),
            listEntity('evidence'),
            listEntity('opportunities'),
            listEntity('policies'),
            listEntity('articles'),
            listEntity('competitors'),
            listEntity('trends'),
            listEntity('recommendations'),
            listEntity('intel_center'),
          ]);
        setState({
          report: dashboard.report,
          counts: {
            证据池: evidence.length,
            机会池: opportunities.length,
            政策倒计时: policies.length,
            文章情报: articles.length,
            竞品动态: competitors.length,
            行业趋势: trends.length,
            推荐配置: recommendations.length,
            情报中心: intel ? '1 行' : '0',
          },
          intelStatus: intel?.overall_status,
        });
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  if (error) return <div className="page"><div className="banner banner-err">{error}</div></div>;
  if (!state) return <div className="page"><p className="muted">加载中…</p></div>;

  return (
    <div className="page">
      <div className="card-grid">
        {Object.entries(state.counts).map(([label, value]) => (
          <div className="stat-card" key={label}>
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {state.report && (
        <div className="panel">
          <div className="panel-header">
            <h3>最新周报 · {state.report.report_id}</h3>
            <span className="muted">截至 {state.report.week_ending}</span>
          </div>
          <p className="judgment">{state.report.one_sentence_judgment}</p>
        </div>
      )}

      {state.intelStatus && (
        <div className="panel">
          <div className="panel-header"><h3>情报中心状态</h3></div>
          <p>{state.intelStatus}</p>
        </div>
      )}
    </div>
  );
}
