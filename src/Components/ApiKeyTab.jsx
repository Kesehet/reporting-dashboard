import React, { useCallback, useEffect, useState } from 'react';
import apiBaseUrl from '../Services/apiBaseUrl';
import sessionHeaders from '../Services/sessionHeaders';

export default function ApiKeyTab() {
  const [keyInfo, setKeyInfo] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(apiBaseUrl() + '/api-key/current', {
        method: 'GET',
        headers: { ...sessionHeaders() },
        credentials: 'same-origin',
        cache: 'no-store',
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Unable to load today\'s API key.');
      setKeyInfo(result);
      setError('');
      setMessage('');
    } catch (err) {
      setKeyInfo(null);
      setError(err.message || 'Unable to load today\'s API key.');
    }
  }, []);

  // Refresh automatically for tabs that remain open across UTC midnight.
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const current = keyInfo?.date === new Date().toISOString().slice(0, 10);
  const copy = async () => {
    if (!current) {
      setMessage('The date changed. Refreshing today\'s key.');
      await refresh();
      return;
    }
    try {
      await navigator.clipboard.writeText(keyInfo.api_key);
      setMessage('Copied to clipboard.');
    } catch (_) {
      setMessage('Clipboard unavailable. Select the key to copy it.');
    }
  };

  return (
    <main className="w3-container" aria-label="API Key">
      <div className="w3-card-4 w3-white" style={{ padding: '24px', maxWidth: '800px' }}>
        <h2 style={{ marginTop: 0 }}>API Key</h2>
        <p style={{ margin: '8px 0 16px' }}>Today's API key (UTC{keyInfo ? ': ' + keyInfo.date : ''})</p>
        {error && <p role="alert" style={{ color: '#a11515' }}>{error}</p>}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          <code aria-label="Today's API key" style={{ flex: '1 1 350px', overflowWrap: 'anywhere', padding: '12px', background: '#f4f4f4', borderRadius: '4px', userSelect: 'all' }}>
            {current ? keyInfo.api_key : (error ? 'Unavailable' : 'Loading…')}
          </code>
          <button type="button" className="w3-button w3-blue" disabled={!current} onClick={copy} aria-label="Copy API key">
            <i className="pi pi-copy" aria-hidden="true" style={{ marginRight: '8px' }} />Copy
          </button>
        </div>
        {message && <p role="status">{message}</p>}
      </div>
    </main>
  );
}
