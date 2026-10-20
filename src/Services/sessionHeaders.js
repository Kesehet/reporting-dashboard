/** LDAP uses a JWT header. Authenticated Microsoft users use their SSO cookie. */
export default function sessionHeaders() {
  const token = localStorage.getItem('token');
  if (!token || localStorage.getItem('login_method') === 'msal') return {};
  return { Authorization: token };
}
