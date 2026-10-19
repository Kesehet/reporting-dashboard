import React, { useCallback, useEffect, useState } from 'react';
import { cryptoRequest } from '../Services/CryptoRotationService';
import '../Styles/cryptoRotation.css';

export default function CryptoRotationTab() {
  const [status, setStatus] = useState(null);
  const [preflight, setPreflight] = useState(null);
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async (signal) => {
    const result = await cryptoRequest('/status', undefined, signal);
    setStatus(result);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    refresh(controller.signal).catch((e) => {
      if (e.name !== 'AbortError') setError(e.message);
    });
    return () => controller.abort();
  }, [refresh]);

  useEffect(() => {
    const jobState = status?.job?.state;
    if (!['running', 'committing', 'starting', 'restoring'].includes(jobState)) return undefined;
    const interval = setInterval(() => refresh().catch((e) => setError(e.message)), 2500);
    return () => clearInterval(interval);
  }, [status?.job?.state, refresh]);

  const action = async (name, path, body, options = {}) => {
    if (busy) return;
    setBusy(name);
    setNotice('');
    setError('');
    try {
      const data = await cryptoRequest(path, body);
      if (name === 'preflight') {
        setPreflight(data);
        setNotice(data.ready ? 'Preflight passed. Existing ciphertext is unchanged.' : 'Preflight blocked. Review failures and configuration before migration.');
      } else {
        setPreflight(null);
        setConfirmation('');
        setNotice(options.message || 'Request accepted. Refresh the job status to monitor progress.');
      }
      if (name === 'migration' || name === 'rollback') {
        setStatus((prev) => ({
          ...prev,
          job: { ...(prev?.job || {}), run_id: data.run_id, state: 'starting' },
        }));
      } else {
        await refresh();
      }
    } catch (e) {
      setError(e.message);
      if (name === 'preflight') setPreflight(null);
    } finally {
      setBusy('');
    }
  };

  const keyring = status?.keyring;
  const job = status?.job;
  const migrating = ['starting', 'running', 'committing', 'restoring'].includes(job?.state);
  const blocked = Boolean(busy || migrating);

  return (
    <main className="crypto-page" aria-label="Encryption administration">
      <header className="crypto-hero">
        <h1>Key Rotation</h1>
      </header>

      {error && <div className="crypto-alert" role="alert">{error}</div>}
      {notice && <div className="crypto-notice" role="status">{notice}</div>}

      <div className="crypto-columns">
        <section className="crypto-panel" aria-label="Historical keyring">
          <div className="crypto-panel-title"><div><h2>Historical keys</h2></div></div>
          <div className="crypto-metrics">
            <div><span>Stored keys</span><strong>{keyring?.keys?.length ?? '—'}</strong></div>
            <div><span>Current key</span><strong className="crypto-small">{keyring?.current_id || 'Not created'}</strong></div>
          </div>
          <div className="crypto-keylist">
            {(keyring?.keys || []).map((item) => (
              <div className="crypto-key" key={item.id}>
                <code>{item.id}</code>
                <span>{item.algorithm}{item.active ? ' · Active' : ' · Historical'}</span>
              </div>
            ))}
          </div>
          <button type="button" disabled={blocked || !status || confirmation !== 'CREATE_GCM_KEY'}
            onClick={() => action('key', '/keys/rotate', { confirm: confirmation }, { message: 'New GCM key archived and activated. Historical keys retained.' })}>
            Create new GCM key
          </button>
        </section>
      </div>

      <section className="crypto-panel" aria-label="Migration control">
        <div className="crypto-panel-title">
          <div><h2>Key Rotation</h2></div>
          <span className="crypto-pill" data-testid="crypto-job-state">{job?.state || 'Not started'}</span>
        </div>
        <div className="crypto-metrics">
          <div><span>Rows scanned</span><strong>{preflight?.scanned ?? job?.processed ?? 0}</strong></div>
          <div><span>Rows updated</span><strong>{job?.updated ?? 0}</strong></div>
          <div><span>Preflight failures</span><strong>{preflight?.failures ?? '—'}</strong></div>
        </div>
        {job?.run_id && <p className="crypto-help">Recovery run ID: <code>{job.run_id}</code></p>}
        {preflight && <div role="status" className="crypto-help"><p>Preflight: {preflight.scanned} rows scanned, {preflight.values_to_rotate} values to rotate, {preflight.failures} failures.</p>{(preflight.examples || []).map((example, idx) => <p key={idx}>{example.table} / {example.column}: {example.error}</p>)}</div>}
        <label htmlFor="crypto-confirm">Confirmation</label>
        <input id="crypto-confirm" type="text" autoComplete="off" spellCheck="false"
          value={confirmation} onChange={(e) => setConfirmation(e.target.value)}
          placeholder="CREATE_GCM_KEY · MIGRATE_PII · RESTORE_ORIGINAL" />
        <div className="crypto-actions">
          <button type="button" disabled={blocked || !status} onClick={() => action('preflight', '/preflight', {})}>
            {busy === 'preflight' ? 'Checking…' : 'Check compatibility'}
          </button>
          <button type="button" disabled={blocked || !preflight?.ready || confirmation !== 'MIGRATE_PII'} onClick={() => action('migration', '/start', { confirm: confirmation })}>
            Migrate now
          </button>
          <button type="button" className="crypto-danger"
            disabled={blocked || confirmation !== 'RESTORE_ORIGINAL' || !job?.run_id || !['completed', 'reconciliation_required', 'restore_failed'].includes(job?.state)}
            onClick={() => action('rollback', '/rollback', { run_id: job.run_id, confirm: confirmation })}>
            Restore previous encryption
          </button>
          <button type="button" className="crypto-quiet" disabled={Boolean(busy)}
            onClick={() => refresh().catch((e) => setError(e.message))}>Refresh status</button>
        </div>
      </section>
    </main>
  );
}
