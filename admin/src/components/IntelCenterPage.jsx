import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import { ENTITIES } from '../entities.js';
import EntityForm from './EntityForm.jsx';

// intel_center is a single-row table: one form over the whole record.
export default function IntelCenterPage() {
  const cfg = ENTITIES.intel_center;
  const [record, setRecord] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    try {
      setRecord(await api(cfg.api));
      setError('');
    } catch (e) {
      setError(e.message);
    }
  }, [cfg.api]);

  useEffect(() => { load(); }, [load]);

  const save = async (payload) => {
    setBusy(true);
    try {
      await api(cfg.api, { method: 'PUT', body: payload });
      setNotice('已保存');
      setTimeout(() => setNotice(''), 3000);
      await load();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      {notice && <div className="banner banner-ok">{notice}</div>}
      {error && <div className="banner banner-err">{error}</div>}
      {!record && !error && <p className="muted">加载中…</p>}
      {record && (
        <div className="panel">
          <div className="panel-header"><h3>情报中心(单行配置)</h3></div>
          <EntityForm fields={cfg.fields} initial={record} submitting={busy} onSubmit={save} />
        </div>
      )}
    </div>
  );
}
