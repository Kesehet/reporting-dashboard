import apiBaseUrl from './apiBaseUrl';

class AuthorizationService {
  constructor(username, password) {
    this.username = username;
    this.password = password;
  }
  clearSession() {
    ['token', 'tokenExpiration', 'display_name', 'login_method'].forEach(
      key => localStorage.removeItem(key)
    );
  }
  isLoggedIn() {
    const token = localStorage.getItem('token');
    const expires = Number(localStorage.getItem('tokenExpiration'));
    if (!token || !Number.isFinite(expires) || expires <= Date.now()) {
      this.clearSession();
      return false;
    }
    return true;
  }
  async checkCredentials() {
    try {
      const response = await fetch(apiBaseUrl() + '/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: this.username, password: this.password }),
      });
      const data = await response.json();
      if (!response.ok || !data.token) return data.message || 'Login failed.';
      localStorage.setItem('token', data.token);
      localStorage.setItem('tokenExpiration', String(data.expires_at || Date.now() + 3600000));
      localStorage.setItem('display_name', data.user || this.username);
      localStorage.setItem('login_method', 'ldap');
      window.location.reload();
      return true;
    } catch (error) {
      return error.message || 'Unable to contact the login server.';
    }
  }
  async logout() {
    const provider = localStorage.getItem('login_method');
    this.clearSession();
    if (provider === 'msal') {
      try {
        const { msalLogoutPopup } = await import('./msalInstance');
        await msalLogoutPopup();
      } catch (error) {
        console.warn('Microsoft logout unavailable:', error);
      }
    }
    window.location.reload();
  }
}
export default AuthorizationService;
