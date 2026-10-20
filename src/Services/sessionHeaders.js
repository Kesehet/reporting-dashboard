/** LDAP keeps Authorization; IIS forwards a dedicated Microsoft ID-token header. */
export default function sessionHeaders() {
  const token = localStorage.getItem('token');
  if (!token) return {};
  return localStorage.getItem('login_method') === 'msal'
    ? { 'X-MSAL-ID-Token': token }
    : { Authorization: token };
}
