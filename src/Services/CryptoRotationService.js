/** Sensitive API requests use an operator-entered, memory-only admin token. */
const baseUrl = () => process.env.NODE_ENV === 'production'
  ? (window.location.href + 'api')
  : 'http://localhost:5000';

export async function cryptoRequest(path, token, body, signal) {
  if (!token || token.length < 32) {
    throw new Error('Enter the administrator token (at least 32 characters).');
  }
  const response = await fetch(baseUrl() + '/crypto' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Crypto-Admin-Token': token,
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    ...(signal ? { signal } : {}),
    cache: 'no-store',
    credentials: 'omit',
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || result.reason || 'Crypto service operation failed.');
  }
  return result;
}
