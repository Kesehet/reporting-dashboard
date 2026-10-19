const baseUrl = () => {
  if (process.env.REACT_APP_API_SERVER_BASE_URL) {
    return process.env.REACT_APP_API_SERVER_BASE_URL.replace(/\/$/, '');
  }
  if (process.env.NODE_ENV !== 'production') return 'http://localhost:5000';
  // Resolve relative to the deployed dashboard directory, not its query or hash.
  return new URL('api', new URL('.', window.location.href)).href.replace(/\/$/, '');
};

export async function cryptoRequest(path, body, signal) {
  const response = await fetch(baseUrl() + '/crypto' + path, {
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
