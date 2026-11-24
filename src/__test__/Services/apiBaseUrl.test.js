import apiBaseUrl, { msalConfigForLocation } from '../../Services/apiBaseUrl';

test.each([
  ['http://localhost:3000/?report=1#summary', 'http://localhost:5000'],
  ['http://127.0.0.1:4173/', 'http://127.0.0.1:5000'],
  ['http://[::1]:3000/', 'http://[::1]:5000'],
  ['https://dev.example.test/index.html?local=true', 'https://dev.example.test/api'],
  ['https://qa.example.test/?report=local#summary', 'https://qa.example.test/api'],
  ['https://prod.example.test:8443/', 'https://prod.example.test:8443/api'],
  ['https://localhost.example.test/', 'https://localhost.example.test/api'],
])('resolves %s to %s', (href, expected) => {
  expect(apiBaseUrl(new URL(href))).toBe(expected);
});

test.each([
  'http://localhost:3000/',
  'https://qa.example.test/index.html?report=1#summary',
  'https://prod.example.test/',
])('uses the actual browser origin for MSAL at %s', href => {
  const location = new URL(href);
  const config = {
    auth: {
      clientId: 'synthetic-client',
      authority: 'https://login.microsoftonline.com/synthetic-tenant',
      redirectUri: 'http://localhost:9999',
      postLogoutRedirectUri: 'http://localhost:9999',
    },
    cache: { cacheLocation: 'localStorage' },
  };
  const resolved = msalConfigForLocation(config, location);
  expect(resolved.auth).toEqual({
    ...config.auth,
    redirectUri: location.origin,
    postLogoutRedirectUri: location.origin,
  });
  expect(resolved.cache).toEqual(config.cache);
  expect(config.auth.redirectUri).toBe('http://localhost:9999');
});
