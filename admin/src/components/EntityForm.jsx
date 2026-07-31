import { useState } from 'react';

function initValues(fields, initial) {
  const values = {};
  for (const f of fields) {
    const v = initial?.[f.name];
    switch (f.type) {
      case 'array':
        values[f.name] = Array.isArray(v) ? v.join('\n') : '';
        break;
      case 'json':
        values[f.name] = v == null ? '' : JSON.stringify(v, null, 2);
        break;
      case 'boolean':
        values[f.name] = !!v;
        break;
      case 'number':
        values[f.name] = v == null ? '' : String(v);
        break;
      default:
        values[f.name] = v ?? '';
    }
  }
  return values;
}

function buildPayload(fields, values) {
  const payload = {};
  for (const f of fields) {
    const raw = values[f.name];
    switch (f.type) {
      case 'boolean':
        payload[f.name] = !!raw;
        break;
      case 'number':
        if (raw !== '') payload[f.name] = Number(raw);
        break;
      case 'array': {
        const items = raw.split('\n').map((s) => s.trim()).filter(Boolean);
        if (items.length > 0 || raw.trim() !== '') payload[f.name] = items;
        break;
      }
      case 'json': {
        if (raw.trim() !== '') {
          try {
            payload[f.name] = JSON.parse(raw);
          } catch {
            throw new Error(`字段「${f.label}」不是合法 JSON`);
          }
        }
        break;
      }
      default:
        if (raw !== '') payload[f.name] = raw;
    }
    if (f.required && payload[f.name] === undefined) {
      throw new Error(`请填写必填字段「${f.label}」`);
    }
  }
  return payload;
}

export default function EntityForm({ fields, initial, pkField, submitting, submitLabel = '保存', onSubmit, onCancel }) {
  const [values, setValues] = useState(() => initValues(fields, initial));
  const [error, setError] = useState('');

  const set = (name, value) => setValues((prev) => ({ ...prev, [name]: value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    try {
      onSubmit(buildPayload(fields, values));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      {fields.map((f) => {
        const disabled = submitting || (initial != null && f.name === pkField);
        return (
          <label key={f.name} className={`form-field${f.type === 'textarea' || f.type === 'array' || f.type === 'json' ? ' form-field-full' : ''}${f.type === 'boolean' ? ' form-field-check' : ''}`}>
            {f.type === 'boolean' ? (
              <>
                <input
                  type="checkbox"
                  checked={!!values[f.name]}
                  disabled={submitting}
                  onChange={(e) => set(f.name, e.target.checked)}
                />
                <span>{f.label}</span>
              </>
            ) : (
              <>
                <span className="form-label">
                  {f.label}
                  {f.required && <em className="required">*</em>}
                </span>
                {f.type === 'select' ? (
                  <select value={values[f.name]} disabled={disabled} onChange={(e) => set(f.name, e.target.value)}>
                    <option value="">(未选择)</option>
                    {f.options.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                ) : f.type === 'textarea' || f.type === 'array' || f.type === 'json' ? (
                  <textarea
                    rows={f.type === 'json' ? 6 : 3}
                    value={values[f.name]}
                    disabled={disabled}
                    placeholder={f.placeholder}
                    onChange={(e) => set(f.name, e.target.value)}
                    className={f.type === 'json' || f.type === 'array' ? 'mono' : ''}
                  />
                ) : (
                  <input
                    type={f.type === 'number' ? 'number' : 'text'}
                    step={f.step}
                    value={values[f.name]}
                    disabled={disabled}
                    placeholder={f.placeholder}
                    onChange={(e) => set(f.name, e.target.value)}
                  />
                )}
                {f.help && <span className="form-help">{f.help}</span>}
              </>
            )}
          </label>
        );
      })}
      {error && <div className="form-error">{error}</div>}
      <div className="form-actions">
        {onCancel && (
          <button type="button" className="btn" onClick={onCancel} disabled={submitting}>取消</button>
        )}
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? '提交中…' : submitLabel}
        </button>
      </div>
    </form>
  );
}
