import sessionHeaders from '../../Services/sessionHeaders';
import ChartDataService from '../../Services/ChartDataService';
import { establishSsoSession } from '../../Services/msalInstance';
import fetchMock from 'jest-fetch-mock';

beforeEach(() => {
  localStorage.clear();
  fetchMock.resetMocks();
  localStorage.setItem('start_date', '2026-10-01');
  localStorage.setItem('end_date', '2026-10-20');
});

test('Microsoft ID token is exchanged once for a server-issued cookie', async () => {
  fetchMock.mockResponseOnce(JSON.stringify({ sso: true }));
  expect(await establishSsoSession('synthetic-id-token')).toBe(true);
  const [url, opts] = fetchMock.mock.calls[0];
  expect(url).toContain('/sso/session');
  expect(opts.credentials).toBe('include');
  expect(opts.method).toBe('POST');
  expect(JSON.parse(opts.body)).toEqual({ id_token: 'synthetic-id-token' });
});

test('SSO chart requests send cookies, no token header or API key', async () => {
  localStorage.setItem('login_method', 'msal');
  localStorage.setItem('token', 'synthetic-msal-id-token');
  expect(sessionHeaders()).toEqual({});
  for (const requestMethod of ['GET', 'POST']) {
    fetchMock.mockResponseOnce(JSON.stringify({ rows: [1] }));
    expect(await new ChartDataService('Test', { requestMethod }).getChart()).toEqual({ rows: [1] });
    const [, opts] = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    expect(opts.credentials).toBe('include');
    expect(opts.headers.Authorization).toBeUndefined();
    expect(opts.headers['X-MSAL-ID-Token']).toBeUndefined();
  }
});

test('LDAP continues sending its JWT and anonymous requests send no token', () => {
  localStorage.setItem('login_method', 'ldap');
  localStorage.setItem('token', 'synthetic-ldap-jwt');
  expect(sessionHeaders()).toEqual({ Authorization: 'synthetic-ldap-jwt' });
  localStorage.removeItem('token');
  expect(sessionHeaders()).toEqual({});
});

test('invalid Microsoft token fails to create the cookie session', async () => {
  fetchMock.mockResponseOnce(JSON.stringify({ error: 'unauthorized' }), { status: 401 });
  await expect(establishSsoSession('fake')).rejects.toThrow(/Unable to establish/);
});
