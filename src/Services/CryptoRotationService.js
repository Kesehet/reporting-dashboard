import apiBaseUrl from './apiBaseUrl';

export async function cryptoRequest(path, body, signal) {
  const response = await fetch(apiBaseUrl() + '/crypto' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      'Content-Type': 'application/json',
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
