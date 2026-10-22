import sessionHeaders from '../../Services/sessionHeaders';
import ChartDataService from '../../Services/ChartDataService';
import fetchMock from 'jest-fetch-mock';

beforeEach(() => {
  fetchMock.enableMocks();
  localStorage.clear();
  fetchMock.resetMocks();
  localStorage.setItem('start_date', '2026-10-01');
  localStorage.setItem('end_date', '2026-10-20');
});

test('MSAL token is included in GET and POST report request headers', async () => {
  localStorage.setItem('login_method', 'msal');
  localStorage.setItem('token', 'synthetic-msal-id-token');
  expect(sessionHeaders()).toEqual({ 'X-MSAL-ID-Token': 'synthetic-msal-id-token' });
  for (const requestMethod of ['GET', 'POST']) {
    fetchMock.mockResponseOnce(JSON.stringify({ rows: [1] }));
    const response = await new ChartDataService('Test', { requestMethod }).getChart();
    expect(response).toEqual({ rows: [1] });
    const [url, options] = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    expect(url).toContain('/charts/Test');
    expect(options.headers['X-MSAL-ID-Token']).toBe('synthetic-msal-id-token');
    expect(options.headers.Authorization).toBeUndefined();
  }
  expect(fetchMock.mock.calls.every(([url]) => !url.includes('/sso/session'))).toBe(true);
});

test('chart requests do not serialize api_key into GET URLs or POST JSON', async () => {
  for (const requestMethod of ['GET', 'POST']) {
    fetchMock.mockResponseOnce(JSON.stringify({ rows: [1] }));
    await new ChartDataService('Test', { requestMethod, api_key: 'must-not-travel', BranchID: '1000' }).getChart();
    const [url, options] = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    expect(url).not.toContain('api_key');
    if (requestMethod === 'POST') {
      expect(JSON.parse(options.body)).not.toHaveProperty('api_key');
      expect(JSON.parse(options.body).BranchID).toBe('1000');
    } else {
      expect(url).toContain('BranchID=1000');
    }
    expect(options.headers).not.toHaveProperty('X-API-KEY');
  }
});

test('LDAP Authorization header unchanged and no token sends no authentication', () => {
  localStorage.setItem('login_method', 'ldap');
  localStorage.setItem('token', 'synthetic-ldap-jwt');
  expect(sessionHeaders()).toEqual({ Authorization: 'synthetic-ldap-jwt' });
  localStorage.removeItem('token');
  expect(sessionHeaders()).toEqual({});
});
