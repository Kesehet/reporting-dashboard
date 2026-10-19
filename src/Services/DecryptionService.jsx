/** Server-side decrypt tool client. Never store or log keys or sensitive strings. */
export default class DecryptionService {
  constructor() {
    const base = process.env.REACT_APP_API_SERVER_BASE_URL ||
      (process.env.NODE_ENV === 'production'
        ? new URL('api', new URL('.', window.location.href)).toString()
        : 'http://localhost:5000');
    this.baseUrl = base.replace(/\/$/, '');
  }

  async decrypt(ciphertext) {
    const response = await fetch(`${this.baseUrl}/tools/decrypt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ciphertext }),
      cache: 'no-store',
    });
    if (!response.ok) {
      if (response.status === 422) throw new Error('Unable to decrypt. Verify the encrypted string and key version.');
      if (response.status === 503) throw new Error('The decryption key is not available on the server.');
      if (response.status === 413) throw new Error('The encrypted string is too large.');
      throw new Error('Decryption request failed. Please try again.');
    }
    let payload;
    try { payload = await response.json(); }
    catch (_) { throw new Error('Invalid decryption response.'); }
    if (!payload || typeof payload.plaintext !== 'string') {
      throw new Error('Invalid decryption response.');
    }
    return payload.plaintext;
  }
}
