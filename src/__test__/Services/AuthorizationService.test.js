import AuthorizationService from '../../Services/AuthorizationService';
import fetchMock from 'jest-fetch-mock';

beforeEach(() => {
  localStorage.clear();
  fetchMock.resetMocks();
});

test('expired or missing sessions require login again', () => {
  const auth = new AuthorizationService('', '');
  expect(auth.isLoggedIn()).toBe(false);
  localStorage.setItem('token', 'test-only-expired');
  localStorage.setItem('tokenExpiration', String(Date.now() - 1000));
  expect(auth.isLoggedIn()).toBe(false);
  expect(localStorage.getItem('token')).toBeNull();
});

test('unexpired token permits the original dashboard session', () => {
  localStorage.setItem('token', 'test-only-token');
  localStorage.setItem('tokenExpiration', String(Date.now() + 3600000));
  expect(new AuthorizationService('', '').isLoggedIn()).toBe(true);
});

test('invalid LDAP credentials do not create a session', async () => {
  fetchMock.mockResponseOnce(JSON.stringify({ message: 'Invalid Credentials!' }), { status: 401 });
  expect(await new AuthorizationService('bad', 'bad').checkCredentials()).not.toBe(true);
  expect(localStorage.getItem('token')).toBeNull();
});
