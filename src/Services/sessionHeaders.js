/** Auth headers for reporting APIs. SSO tokens must survive IIS/ARR proxies. */
export default function sessionHeaders() {
  const token = localStorage.getItem('token');
  if (!token) return {};
  return localStorage.getItem('login_method') === 'msal'
    ? { 'X-MSAL-ID-Token': token }
    : { Authorization: token };
}
