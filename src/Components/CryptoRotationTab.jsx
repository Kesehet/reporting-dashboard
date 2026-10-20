import React, { useCallback, useEffect, useState } from 'react';
import { cryptoRequest } from '../Services/CryptoRotationService';
import '../Styles/cryptoRotation.css';

export default function CryptoRotationTab() {
  const [status, setStatus] = useState(null);
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
    if (!['starting', 'running', 'committing', 'restoring'].includes(jobState)) return undefined;
    const interval = setInterval(() => refresh().catch((e) => setError(e.message)), 2500);
    return () => clearInterval(interval);
  }, [status?.job?.state, refresh]);

  const action = async (name, path, body) => {
    if (busy) return;
    setBusy(name);
    setNotice('');
    setError('');
    try {
      const data = await cryptoRequest(path, body);
      setStatus((prev) => ({
        ...prev,
        job: { ...(prev?.job || {}), run_id: data.run_id, state: name === 'restore' ? 'restoring' : 'starting' },
      }));
      setNotice(name === 'rotate' ? 'Rotation started.' : 'Restore started.');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy('');
    }
  };

  const keyring = status?.keyring;
  const job = status?.job;
  const migrating = ['starting', 'running', 'committing', 'restoring'].includes(job?.state);
  const needsReview = ['reconciliation_required', 'restore_failed'].includes(job?.state);
  const blocked = Boolean(busy || migrating);
  const canRestore = Boolean(job?.run_id && ['completed', 'reconciliation_required', 'restore_failed'].includes(job?.state));

  return (
    <main className="crypto-page" aria-label="Encryption administration">
      <header className="crypto-hero"><h1>Key Rotation</h1></header>
      {error && <div className="crypto-alert" role="alert">{error}</div>}
      {notice && <div className="crypto-notice" role="status">{notice}</div>}
      {job?.error && <div className="crypto-alert" role="alert">{job.error}</div>}

      <section className="crypto-panel" aria-label="Key rotation controls">
        <div className="crypto-panel-title">
          <h2>Key Rotation</h2>
          <span className="crypto-pill" data-testid="crypto-job-state">{job?.state || 'Not started'}</span>
        </div>
        <div className="crypto-actions">
          <button type="button" disabled={blocked || !status || needsReview}
            onClick={() => action('rotate', '/rotate', {})}>
            {busy === 'rotate' ? 'Starting…' : 'Rotate'}
          </button>
          <button type="button" className="crypto-danger"
            disabled={blocked || !canRestore}
            onClick={() => action('restore', '/rollback', { run_id: job.run_id, confirm: 'RESTORE_ORIGINAL' })}>
            {busy === 'restore' ? 'Starting…' : 'Restore'}
          </button>
        </div>
        <div className="crypto-metrics">
          <div><span>Rows scanned</span><strong>{job?.preflight?.scanned ?? job?.processed ?? 0}</strong></div>
          <div><span>Rows updated</span><strong>{job?.updated ?? 0}</strong></div>
          <div><span>Preflight failures</span><strong>{job?.preflight?.failures ?? '—'}</strong></div>
        </div>
        {job?.run_id && <p className="crypto-help">Recovery run ID: <code>{job.run_id}</code></p>}
        {(job?.preflight?.examples || []).map((example, idx) => (
          <p className="crypto-help" key={idx}>{example.table} / {example.column}: {example.error}</p>
        ))}
      </section>

      <section className="crypto-panel" aria-label="Historical keyring">
        <div className="crypto-panel-title"><h2>Historical keys</h2></div>
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
      </section>
    </main>
  );
}
