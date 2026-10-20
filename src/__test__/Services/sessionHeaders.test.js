import sessionHeaders from '../../Services/sessionHeaders';
import ChartDataService from '../../Services/ChartDataService';
import fetchMock from 'jest-fetch-mock';

beforeEach(() => {
  localStorage.clear();
  fetchMock.resetMocks();
  localStorage.setItem('start_date', '2026-10-01');
  localStorage.setItem('end_date', '2026-10-20');
});

test('Microsoft SSO uses IIS-compatible header and never a static token', async () => {
  localStorage.setItem('login_method', 'msal');
  localStorage.setItem('token', 'synthetic-msal-id-token');
  expect(sessionHeaders()).toEqual({ 'X-MSAL-ID-Token': 'synthetic-msal-id-token' });
  for (const requestMethod of ['GET', 'POST']) {
    fetchMock.mockResponseOnce(JSON.stringify({ rows: [1] }));
    const response = await new ChartDataService('Test', { requestMethod }).getChart();
    expect(response).toEqual({ rows: [1] });
    const [, options] = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    expect(options.headers['X-MSAL-ID-Token']).toBe('synthetic-msal-id-token');
    expect(options.headers.Authorization).toBeUndefined();
  }
});

test('LDAP still uses Authorization and anonymous requests send no auth', () => {
  localStorage.setItem('login_method', 'ldap');
  localStorage.setItem('token', 'synthetic-ldap-jwt');
  expect(sessionHeaders()).toEqual({ Authorization: 'synthetic-ldap-jwt' });
  localStorage.removeItem('token');
  expect(sessionHeaders()).toEqual({});
});
