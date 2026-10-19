import React, { useState } from 'react';
import DecryptionService from '../Services/DecryptionService';

const service = new DecryptionService();

export default function BusinessStringDecryptionTab() {
  const [ciphertext, setCiphertext] = useState('');
  const [token, setToken] = useState('');
  const [plaintext, setPlaintext] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);

  const resetResult = () => {
    setPlaintext(null);
    setError('');
    setCopied(false);
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    resetResult();
    if (busy || !ciphertext.trim() || !token) return;
    setBusy(true);
    try {
      setPlaintext(await service.decrypt(ciphertext.trim(), token));
    } catch (requestError) {
      setError(requestError.message || 'Decryption request failed.');
    } finally {
      setBusy(false);
    }
  };

  const clearAll = () => {
    setCiphertext('');
    setToken('');
    resetResult();
  };

  const copyResult = async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(plaintext);
      setCopied(true);
      setError('');
    } catch (_) {
      setError('Clipboard is unavailable. Select and copy the result manually.');
    }
  };

  return (
    <div className="w3-container w3-card-4" style={{ padding: '24px', maxWidth: '920px', margin: '0 auto' }}>
      <h2 className="w3-center">Business String Decryption</h2>
      <form onSubmit={onSubmit} autoComplete="off" style={{ display: 'grid', gap: '14px' }}>
        <label htmlFor="decrypt-token" style={{ fontWeight: 600 }}>Tool access token</label>
        <input
          id="decrypt-token" type="password" autoComplete="off"
          value={token} disabled={busy}
          onChange={(event) => { setToken(event.target.value); resetResult(); }}
          placeholder="Enter authorized access token"
          style={{ padding: '12px', border: '1px solid #ced4da', borderRadius: '6px' }}
        />
        <label htmlFor="decrypt-input" style={{ fontWeight: 600 }}>Encrypted string</label>
        <textarea
          id="decrypt-input" rows={5} spellCheck={false} value={ciphertext} disabled={busy}
          onChange={(event) => { setCiphertext(event.target.value); resetResult(); }}
          placeholder="Paste encrypted string (v2:...)"
          style={{ padding: '12px', border: '1px solid #ced4da', borderRadius: '6px', overflowWrap: 'anywhere' }}
        />
        <div style={{ display: 'flex', gap: '12px' }}>
          <button type="submit" className="w3-button w3-blue"
            disabled={busy || !ciphertext.trim() || !token}
            style={{ borderRadius: '6px' }}>
            {busy ? 'Decrypting...' : 'Decrypt string'}
          </button>
          <button type="button" className="w3-button w3-light-grey"
            onClick={clearAll} disabled={busy} style={{ borderRadius: '6px' }}>
            Clear all
          </button>
        </div>
      </form>
      {error && <p role="alert" style={{ color: '#b42318' }}>{error}</p>}
      {plaintext !== null && (
        <section aria-label="Decryption result" style={{ marginTop: '24px' }}>
          <label htmlFor="decrypt-output" style={{ display: 'block', fontWeight: 600 }}>Decrypted string</label>
          <textarea id="decrypt-output" rows={5} value={plaintext} readOnly
            style={{ width: '100%', marginTop: '10px', padding: '12px', border: '1px solid #ced4da', borderRadius: '6px' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '10px' }}>
            <button type="button" className="w3-button w3-light-grey" onClick={copyResult}>Copy result</button>
            {copied && <span role="status">Copied</span>}
          </div>
        </section>
      )}
    </div>
  );
}
