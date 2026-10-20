import { PublicClientApplication, EventType } from '@azure/msal-browser';
import apiBaseUrl from './apiBaseUrl';

let clientPromise;
let interactionInProgress = false;

export async function ensureMsal() {
  if (!clientPromise) {
    clientPromise = (async () => {
      const response = await fetch(apiBaseUrl() + '/msalConfig');
      if (!response.ok) throw new Error('Microsoft SSO is not configured.');
      const client = new PublicClientApplication(await response.json());
      await client.initialize();
      client.addEventCallback(event => {
        if ([EventType.LOGIN_START, EventType.ACQUIRE_TOKEN_START, EventType.LOGOUT_START].includes(event.eventType)) {
          interactionInProgress = true;
        } else if ([EventType.LOGIN_SUCCESS, EventType.LOGIN_FAILURE, EventType.ACQUIRE_TOKEN_SUCCESS,
          EventType.ACQUIRE_TOKEN_FAILURE, EventType.LOGOUT_SUCCESS, EventType.LOGOUT_FAILURE].includes(event.eventType)) {
          interactionInProgress = false;
        }
      });
      return client;
    })().catch(error => { clientPromise = null; throw error; });
  }
  return clientPromise;
}

export function storeMsalSession(result) {
  const token = result?.idToken;
  const account = result?.account;
  if (!token || !account) throw new Error('Microsoft did not return a sign-in token.');
  const expiry = Number(result.idTokenClaims?.exp || account.idTokenClaims?.exp) * 1000;
  if (!expiry || expiry <= Date.now()) throw new Error('Microsoft sign-in token has expired.');
  localStorage.setItem('token', token);
  localStorage.setItem('tokenExpiration', String(expiry));
  localStorage.setItem('display_name', account.name || account.username);
  localStorage.setItem('login_method', 'msal');
}

export async function bootMsalActiveAccount() {
  const client = await ensureMsal();
  const redirect = await client.handleRedirectPromise();
  if (redirect?.account) {
    client.setActiveAccount(redirect.account);
    storeMsalSession(redirect);
    return redirect.account;
  }
  const account = client.getActiveAccount() || client.getAllAccounts()[0];
  if (!account) return null;
  client.setActiveAccount(account);
  if (!localStorage.getItem('token')) {
    try {
      const session = await client.acquireTokenSilent({ account, scopes: ['openid', 'profile', 'email'] });
      storeMsalSession(session);
    } catch (error) {
      return null;
    }
  }
  return account;
}

export async function msalLoginPopup() {
  const client = await ensureMsal();
  if (interactionInProgress) throw new Error('Microsoft sign-in is already in progress.');
  try {
    const result = await client.loginPopup({ scopes: ['openid', 'profile', 'email'], prompt: 'select_account' });
    client.setActiveAccount(result.account);
    storeMsalSession(result);
    return result;
  } catch (error) {
    if (['popup_window_error', 'popup_window_open_error'].includes(error?.errorCode)) {
      await client.loginRedirect({ scopes: ['openid', 'profile', 'email'], prompt: 'select_account' });
      return null;
    }
    throw error;
  }
}

export async function msalLogoutPopup() {
  const client = await ensureMsal();
  const account = client.getActiveAccount() || client.getAllAccounts()[0];
  if (account) await client.logoutPopup({ account });
}
