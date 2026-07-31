import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import Modal from './Modal.jsx';
import EntityForm from './EntityForm.jsx';

// Generic list + create/edit/delete page driven entirely by an entity config.
export default function EntityPage({ config }) {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState(null); // { mode: 'create'|'edit', row? }
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const data = await api(config.api);
      setRows(config.listFrom ? config.listFrom(data) : data);
    } catch (e) {
      setError(e.message);
      setRows([]);
    }
  }, [config]);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => JSON.stringify(r).toLowerCase().includes(q));
  }, [rows, query]);

  const flash = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 3000);
  };

  const submit = async (payload) => {
    setBusy(true);
    try {
      if (modal.mode === 'create') {
        await api(config.api, { method: 'POST', body: payload });
        flash('已创建');
      } else {
        const id = modal.row[config.pk];
        await api(`${config.api}/${encodeURIComponent(id)}`, { method: 'PUT', body: payload });
        flash('已保存');
      }
      setModal(null);
      await load();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async () => {
    setBusy(true);
    try {
      const id = deleteTarget[config.pk];
      await api(`${config.api}/${encodeURIComponent(id)}`, { method: 'DELETE' });
      flash(`已删除 ${id}`);
      setDeleteTarget(null);
      await load();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  const displayPk = (row) => {
    const v = row[config.pk];
    return v === undefined ? '(无 id)' : String(v);
  };

  return (
    <div className="page">
      <div className="page-toolbar">
        <input
          className="search-input"
          placeholder={`搜索${config.label}…`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <span className="row-count">{filtered.length} / {rows?.length ?? 0} 条</span>
        <button className="btn btn-primary" onClick={() => setModal({ mode: 'create' })}>+ 新增</button>
      </div>

      {config.readonlyExisting && (
        <div className="banner banner-warn">{config.readonlyExisting}</div>
      )}
      {notice && <div className="banner banner-ok">{notice}</div>}
      {error && <div className="banner banner-err">{error}</div>}

      {rows === null ? (
        <p className="muted">加载中…</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {config.columns.map((c) => <th key={c.key}>{c.label}</th>)}
                <th className="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={config.columns.length + 1} className="muted center">暂无数据</td></tr>
              )}
              {filtered.map((row, i) => (
                <tr key={row[config.pk] ?? i}>
                  {config.columns.map((c) => (
                    <td key={c.key}>{c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '')}</td>
                  ))}
                  <td className="col-actions">
                    {config.readonlyExisting && row[config.pk] === undefined ? (
                      <span className="muted">—</span>
                    ) : (
                      <>
                        <button className="btn btn-sm" onClick={() => setModal({ mode: 'edit', row })}>编辑</button>
                        <button className="btn btn-sm btn-danger" onClick={() => setDeleteTarget(row)}>删除</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <Modal
          wide
          title={`${modal.mode === 'create' ? '新增' : '编辑'}${config.label}${modal.row ? `: ${displayPk(modal.row)}` : ''}`}
          onClose={() => setModal(null)}
        >
          <EntityForm
            fields={config.fields}
            initial={modal.mode === 'edit' ? modal.row : null}
            pkField={config.pk}
            submitting={busy}
            onSubmit={submit}
            onCancel={() => setModal(null)}
          />
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="确认删除" onClose={() => setDeleteTarget(null)}>
          <p>
            确定要删除{config.label} <strong>{displayPk(deleteTarget)}</strong> 吗?此操作不可撤销。
          </p>
          <div className="form-actions">
            <button className="btn" onClick={() => setDeleteTarget(null)} disabled={busy}>取消</button>
            <button className="btn btn-danger" onClick={doDelete} disabled={busy}>
              {busy ? '删除中…' : '确认删除'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
