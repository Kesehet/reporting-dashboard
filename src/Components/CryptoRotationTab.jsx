import React, { useCallback, useEffect, useState } from 'react';
import { cryptoRequest } from '../Services/CryptoRotationService';
import '../Styles/cryptoRotation.css';

export default function CryptoRotationTab() {
  const [token, setToken] = useState('');
  const [status, setStatus] = useState(null);
  const [preflight, setPreflight] = useState(null);
  const [ciphertext, setCiphertext] = useState('');
  const [plaintext, setPlaintext] = useState('');
  const [reveal, setReveal] = useState(false);
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    if (!token) return;
    const result = await cryptoRequest('/status', token);
    setStatus(result);
  }, [token]);

  useEffect(() => {
    setStatus(null);
    setPreflight(null);
    setPlaintext('');
    setReveal(false);
    setError('');
    if (!token || token.length < 32) return undefined;
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      cryptoRequest('/status', token, undefined, controller.signal)
        .then(setStatus)
        .catch((e) => { if (e.name !== 'AbortError') setError(e.message); });
    }, 350);
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [token]);

  useEffect(() => {
    const jobState = status?.job?.state;
    if (!token || !['running', 'committing', 'starting'].includes(jobState)) return undefined;
    const interval = setInterval(() => refresh().catch((e) => setError(e.message)), 2500);
    return () => clearInterval(interval);
  }, [status?.job?.state, token, refresh]);

  const action = async (name, path, body, options = {}) => {
    if (busy) return;
    setBusy(name);
    setNotice('');
    setError('');
    try {
      const data = await cryptoRequest(path, token, body);
      if (name === 'decrypt') {
        setPlaintext(data.plaintext);
        setReveal(false);
      } else if (name === 'preflight') {
        setPreflight(data);
        setNotice(data.ready ? 'Preflight passed. Existing ciphertext is unchanged.' : 'Preflight blocked. Review failures and configuration before migration.');
      } else {
        setPreflight(null);
        setConfirmation('');
        setNotice(options.message || 'Request accepted. Refresh the job status to monitor progress.');
      }
      await refresh();
    } catch (e) {
      setError(e.message);
      if (name === 'preflight') setPreflight(null);
      if (name === 'decrypt') setPlaintext('');
    } finally {
      setBusy('');
    }
  };

  const keyring = status?.keyring;
  const job = status?.job;
  const migrating = ['starting', 'running', 'committing'].includes(job?.state);
  const blocked = Boolean(busy || migrating);

  return (
    <main className="crypto-page" aria-label="Encryption administration">
      <header className="crypto-hero">
        <span className="crypto-eyebrow">ADMINISTRATION / ENCRYPTION</span>
        <h1>Encryption &amp; Key Rotation</h1>
        <p>Decrypt a value, review historical keys, and migrate PII safely without changing SQL schemas.</p>
      </header>

      <section className="crypto-panel" aria-label="Administrator access">
        <div className="crypto-panel-title">
          <div><h2>Administrator access</h2><p>The token stays in this tab's memory and is never saved in browser storage.</p></div>
          {status && <span className="crypto-pill">Connected</span>}
        </div>
        <label htmlFor="crypto-token">Administrator token</label>
        <input id="crypto-token" type="password" autoComplete="off" spellCheck="false"
          value={token} onChange={(e) => setToken(e.target.value)} placeholder="Enter private admin token" />
        <div className="crypto-actions">
          <button type="button" disabled={Boolean(busy) || token.length < 32} onClick={() => action('refresh', '/status')}>Refresh status</button>
          <button type="button" className="crypto-quiet" onClick={() => { setToken(''); setPlaintext(''); setCiphertext(''); }}>Clear session</button>
        </div>
      </section>

      {error && <div className="crypto-alert" role="alert">{error}</div>}
      {notice && <div className="crypto-notice" role="status">{notice}</div>}

      <div className="crypto-columns">
        <section className="crypto-panel" aria-label="Decrypt encrypted string">
          <div className="crypto-panel-title"><div><h2>Decrypt string</h2><p>Uses the matching historical key, if available. No plaintext is logged or saved.</p></div></div>
          <label htmlFor="crypto-ciphertext">Encrypted value</label>
          <textarea id="crypto-ciphertext" rows="5" value={ciphertext} spellCheck="false"
            onChange={(e) => { setCiphertext(e.target.value); setPlaintext(''); setReveal(false); }}
            placeholder="Paste ciphertext here" />
          <div className="crypto-actions">
            <button type="button" disabled={blocked || !ciphertext.trim() || !status} onClick={() => action('decrypt', '/decrypt', { value: ciphertext.trim() })}>
              {busy === 'decrypt' ? 'Decrypting…' : 'Decrypt value'}
            </button>
            <button type="button" className="crypto-quiet" onClick={() => { setCiphertext(''); setPlaintext(''); }}>Clear</button>
          </div>
          {plaintext !== '' && <div className="crypto-output">
            <div className="crypto-panel-title"><strong>Decrypted value</strong>
              <button type="button" className="crypto-quiet" onClick={() => setReveal((value) => !value)}>{reveal ? 'Hide' : 'Reveal'}</button>
            </div>
            <div className="crypto-result" aria-label="Decryption result">{reveal ? plaintext : '••••••••••••••••'}</div>
          </div>}
        </section>

        <section className="crypto-panel" aria-label="Historical keyring">
          <div className="crypto-panel-title"><div><h2>Historical keyring</h2><p>All imported keys remain available for older records.</p></div></div>
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
          <p className="crypto-help">Secrets are not returned to the browser. Import older key files on the server before migration.</p>
          <button type="button" disabled={blocked || !status || confirmation !== 'CREATE_GCM_KEY'}
            onClick={() => action('key', '/keys/rotate', { confirm: confirmation }, { message: 'New GCM key archived and activated. Historical keys retained.' })}>
            Create &amp; activate new GCM key
          </button>
        </section>
      </div>

      <section className="crypto-panel" aria-label="Migration control">
        <div className="crypto-panel-title">
          <div><h2>Production migration</h2><p>Encrypted recovery journal, SQL transaction rollback on failure, and strict column-capacity checks.</p></div>
          <span className="crypto-pill">{job?.state || 'Not started'}</span>
        </div>
        <div className="crypto-steps">
          <div><span className="crypto-step">01</span><strong>Prepare</strong><p>Preserve keyring backups and pause competing ETL writers.</p></div>
          <div><span className="crypto-step">02</span><strong>Preflight</strong><p>Decrypt every value, validate existing column widths, and identify failures.</p></div>
          <div><span className="crypto-step">03</span><strong>Migrate</strong><p>Re-encrypt in one transaction, verify and securely journal originals.</p></div>
          <div><span className="crypto-step">04</span><strong>Verify / restore</strong><p>Review results and retain rollback files.</p></div>
        </div>
        <div className="crypto-metrics">
          <div><span>Rows scanned</span><strong>{job?.processed ?? 0}</strong></div>
          <div><span>Rows updated</span><strong>{job?.updated ?? 0}</strong></div>
          <div><span>Preflight failures</span><strong>{preflight?.failures ?? '—'}</strong></div>
        </div>
        {job?.run_id && <p className="crypto-help">Recovery run ID: <code>{job.run_id}</code></p>}
        {preflight && <div role="status" className="crypto-help"><p>Preflight: {preflight.scanned} rows scanned, {preflight.values_to_rotate} values to rotate, {preflight.failures} failures.</p>{(preflight.examples || []).map((example, idx) => <p key={idx}>{example.table} / {example.column}: {example.error}</p>)}</div>}
        <label htmlFor="crypto-confirm">Type the exact confirmation required for your next action</label>
        <input id="crypto-confirm" type="text" autoComplete="off" spellCheck="false"
          value={confirmation} onChange={(e) => setConfirmation(e.target.value)}
          placeholder="CREATE_GCM_KEY · MIGRATE_PII · RESTORE_ORIGINAL" />
        <div className="crypto-actions">
          <button type="button" disabled={blocked || !status} onClick={() => action('preflight', '/preflight', {})}>
            {busy === 'preflight' ? 'Checking…' : 'Run read-only preflight'}
          </button>
          <button type="button" disabled={blocked || !preflight?.ready || confirmation !== 'MIGRATE_PII'} onClick={() => action('migration', '/start', { confirm: confirmation })}>
            Start checked migration
          </button>
          <button type="button" className="crypto-danger"
            disabled={blocked || confirmation !== 'RESTORE_ORIGINAL' || !job?.run_id || !['completed', 'reconciliation_required'].includes(job?.state)}
            onClick={() => action('rollback', '/rollback', { run_id: job.run_id, confirm: confirmation })}>
            Restore original ciphertext
          </button>
        </div>
        <p className="crypto-help">Preflight does not change data. Stop other database writers for the production run. A missing key, unrecognized ciphertext, oversized value, or conflicting update blocks migration.</p>
      </section>
    </main>
  );
}
