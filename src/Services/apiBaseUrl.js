export default function apiBaseUrl() {
  const configured = process.env.REACT_APP_API_SERVER_BASE_URL;
  if (configured) return configured.replace(/\/$/, '');
  if (process.env.NODE_ENV !== 'production') return 'http://localhost:5000';
  const path = window.location.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '');
  return window.location.origin + path + '/api';
}
