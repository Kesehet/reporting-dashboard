// src/Components/ReportLoginComponent.jsx
import { useEffect, useState } from "react";
import { InputText } from "primereact/inputtext";
import { Button } from "primereact/button";

import FNBlogo from "./../Images/FNBlogo-long.png";
import AuthorizationService from "../Services/AuthorizationService";

import "primereact/resources/themes/nova/theme.css";
import "primereact/resources/primereact.min.css";
import "../primeflex.css";
import "primeicons/primeicons.css";
import "../Styles/loginScn.css";

import {
  msalLoginPopup,
  msalLogoutPopup,
  bootMsalActiveAccount,
} from "../Services/msalInstance";


const ReportLoginComponent = () => {
  const [userEmail, setUserEmail] = useState("");
  const [userPassword, setUserPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [msAccount, setMsAccount] = useState(null);
  const [msBusy, setMsBusy] = useState(false); // prevents double popups

  // Try restoring active account at mount (prevents redundant logins)
  useEffect(() => {
    (async () => {
      try {
        const before = localStorage.getItem('token');
        const account = await bootMsalActiveAccount();
        if (account) setMsAccount(account);
        if (!before && localStorage.getItem('token')) window.location.reload();
      } catch (e) {
        // Non-fatal: log to console to avoid noisy UI
        // eslint-disable-next-line no-console
        console.warn("MSAL boot failed:", e);
      }
    })();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    const authService = new AuthorizationService(userEmail, userPassword);
    authService
      .checkCredentials()
      .then((response) => {
        if (response === true) setErrorMessage("");
        else setErrorMessage(response || "An unknown error occurred");
      })
      .catch((error) => setErrorMessage(error.message || "An error occurred"))
      .finally(() => {
        setIsSubmitting(false);
        setUserEmail("");
        setUserPassword("");
      });
  };

  // --- Microsoft sign-in handlers ---
  const handleMicrosoftLogin = async () => {
    if (msBusy) return;
    try {
      setMsBusy(true);
      setErrorMessage("");
      const result = await msalLoginPopup(); // null if redirect fallback occurs
      if (result?.account) {
        setMsAccount(result.account);
        window.location.reload();
      }
    } catch (e) {
      setErrorMessage(e?.message || "Microsoft login failed");
    } finally {
      setMsBusy(false);
    }
  };

  const handleMicrosoftLogout = async () => {
    if (msBusy) return;
    try {
      setMsBusy(true);
      await msalLogoutPopup();
      new AuthorizationService('', '').clearSession();
      setMsAccount(null);
    } catch (e) {
      setErrorMessage(e?.message || "Microsoft logout failed");
    } finally {
      setMsBusy(false);
    }
  };

  return (
    <div
      className="w3-container"
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <div
        className="p-card"
        style={{
          padding: "2rem",
          boxShadow: "0 2px 5px rgba(0,0,0,0.2)",
          borderRadius: "8px",
          backgroundColor: "white",
          maxWidth: "400px",
          width: "100%",
        }}
      >
        <header
          className="headerSector-login"
          style={{ textAlign: "center", marginBottom: "1rem" }}
        >
          <img
            src={FNBlogo}
            alt="First National Bank, Pennsylvania Logo"
            width={"100%"}
            className="header-logo-login"
          />
          <div className="report-title-login">
            <h1 style={{ fontSize: "1.5rem", margin: "0.5rem 0" }}>
              Welcome Back to the Reporting Dashboard
            </h1>
          </div>
        </header>

        <div className="user-login">
          {errorMessage && (
            <div
              style={{
                color: "red",
                background: "white",
                padding: "5px",
                borderRadius: "5px",
                marginBottom: "1rem",
                textAlign: "center",
              }}
              className="w3-animate-zoom"
            >
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label htmlFor="email" className="email-label">
              User Name
            </label>
            <InputText
              id="email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              type="text"
              placeholder="User Name"
              className="w-full mb-3"
              disabled={isSubmitting}
            />

            <label htmlFor="password" className="password-label">
              Password
            </label>
            <InputText
              id="password"
              value={userPassword}
              onChange={(e) => setUserPassword(e.target.value)}
              type="password"
              placeholder="Password"
              className="w-full mb-3"
              disabled={isSubmitting}
            />

            <Button
              label="Sign In"
              icon="pi pi-user"
              className="login-button"
              type="submit"
              disabled={isSubmitting}
              style={{ width: "100%" }}
            />
          </form>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <Button
            label={msBusy ? "Opening Microsoft Login..." : "SSO Sign In"}
            icon="pi pi-microsoft"
            className="login-button"
            type="button" // IMPORTANT: prevent implicit form submit
            onClick={handleMicrosoftLogin}
            disabled={msBusy}
            style={{ width: "100%" }}
          />
        </div>

        {msAccount && (
          <div style={{ marginTop: "1rem", textAlign: "center" }}>
            <div style={{ marginBottom: "0.5rem" }}>
              Signed in as <b>{msAccount.username || msAccount.name}</b>
            </div>
            <Button
              label={msBusy ? "Signing out..." : "Sign Out of Microsoft"}
              icon="pi pi-sign-out"
              className="p-button-secondary"
              type="button"
              onClick={handleMicrosoftLogout}
              disabled={msBusy}
              style={{ width: "100%" }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportLoginComponent;