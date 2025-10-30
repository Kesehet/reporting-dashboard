// src/Services/msalInstance.jsx
import {
  PublicClientApplication,
  EventType,
} from "@azure/msal-browser";
console.log(
  await (
    await fetch(
      process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000" + "/msalConfig"
    )
  ).json()
)
export const msalInstance = new PublicClientApplication(
  await (
    await fetch(
      process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000" + "/msalConfig"
    )
  ).json());

msalInstance.clearCache()
console.log(msalInstance.getLogger().info("Resetting interaction state if stuck"))

// ---- Internal interaction guard synced with MSAL events ----
let interactionInProgress = false;
let eventsWired = false;

// Call once somewhere early (or lazy before first use)
export async function ensureMsal() {
  if (msalInstance._initialized) return;
  await msalInstance.initialize();
  msalInstance._initialized = true;

  if (!eventsWired) {
    msalInstance.addEventCallback((event) => {
      // START of interactive flows
      if (
        event.eventType === EventType.LOGIN_START ||
        event.eventType === EventType.ACQUIRE_TOKEN_START ||
        event.eventType === EventType.LOGOUT_START
      ) {
        interactionInProgress = true;
      }

      // END of interactive flows (both success and failure)
      if (
        event.eventType === EventType.LOGIN_SUCCESS ||
        event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS ||
        event.eventType === EventType.LOGOUT_SUCCESS ||
        event.eventType === EventType.LOGIN_FAILURE ||
        event.eventType === EventType.ACQUIRE_TOKEN_FAILURE ||
        event.eventType === EventType.LOGOUT_FAILURE
      ) {
        interactionInProgress = false;
      }
    });
    eventsWired = true;
  }
}

// Optionally restore active account from cache on startup
export async function bootMsalActiveAccount() {
  await ensureMsal();
  if (!msalInstance.getActiveAccount()) {
    const acc = msalInstance.getAllAccounts()[0];
    if (acc) msalInstance.setActiveAccount(acc);
  }
}

export async function getAccountData() {
  await ensureMsal();
  const acc =
    msalInstance.getActiveAccount() ??
    msalInstance.getAllAccounts()[0] ??
    null;
    console.log(acc);
  return acc;
}

export async function msalIsLoggedIn() {
  await ensureMsal();
  return !!(await getAccountData());
}

export async function msalLoginPopup() {
  await ensureMsal();

  if (interactionInProgress) {
    throw new Error(
      "Another Microsoft sign-in is already in progress. Please close any open sign-in windows and try again."
    );
  }

  try {
    const resp = await msalInstance.loginPopup({
      scopes: ["openid", "profile", "email"],
      prompt: "select_account",
    });
    msalInstance.setActiveAccount(resp.account);
    return resp.account;
  } catch (e) {
    const code = e?.errorCode || e?.name || "";
    // Fallback to redirect if popup is blocked/cancelled by policy/user
    if (
      code.includes("popup_window_error") ||
      code.includes("popup_window_open_error") ||
      code.includes("user_cancelled")
    ) {
      await msalInstance.loginRedirect({
        scopes: ["openid", "profile", "email"],
        prompt: "select_account",
      });
      return null; // flow resumes after redirect
    }
    throw e;
  }
}

export async function msalLogoutPopup() {
  await ensureMsal();

  if (interactionInProgress) {
    throw new Error(
      "A Microsoft authentication interaction is currently in progress. Try again in a moment."
    );
  }

  const account = await getAccountData();
  if (account) {
    await msalInstance.logoutPopup({ account });
  }
}
