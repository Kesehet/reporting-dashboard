// The same bundle runs locally and behind the DEV/QA/PROD reverse proxy.
export default function apiBaseUrl(location = window.location) {
  const { hostname, protocol, origin } = location;
  const isLocal = ['localhost', '127.0.0.1', '[::1]'].includes(hostname);
  return isLocal ? `${protocol}//${hostname}:5000` : `${origin}/api`;
}

export function msalConfigForLocation(config, location = window.location) {
  return {
    ...config,
    auth: {
      ...config.auth,
      redirectUri: location.origin,
      postLogoutRedirectUri: location.origin,
    },
  };
}
