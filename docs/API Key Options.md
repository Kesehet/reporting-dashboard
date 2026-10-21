# API Access Security – Possible Approaches

We have three possible approaches to secure the Reporting Dashboard APIs. The main requirement is to make sure that only authorized users can access the APIs, and someone who doesn't have dashboard access should not be able to directly call the API URLs.

Below are the options, how they would work, and the pros and cons of each.

## Option 1: Rotate the API Key Every 24 Hours

In this approach, we can automatically generate a new API key every 24 hours. The old key will expire, and only the latest key can be used to access the APIs.

**How it will work:**

1. A scheduler will generate a new random API key every 24 hours.
2. The backend will store the new key securely and invalidate the previous one.
3. We can expose a protected endpoint to get the latest key, but only users who are already logged into the dashboard can access it.
4. The user can then pass this key in the API URL, for example:
   `/charts/BusinessSummary?api_key=CURRENT_KEY`
5. For any automated jobs or external services, we will need a separate secure way to retrieve the latest key.

**Advantages:**
- Easy to implement with minimal changes to the existing system.
- No need to maintain a separate user database.
- Even if the key gets exposed, it will only be valid for a limited time.
- We can continue using most of the existing API implementation.

**Limitations:**
- If someone gets the current key, they can still access the APIs until that key expires.
- The key can get exposed through URLs, logs, or browser history.
- Since the same key is shared, we cannot identify which user is making a request.
- Any integrations using the key will need to update it every day.

**My view:** This is probably the easiest option to implement, but it doesn't completely solve the security concern. We are only reducing how long an exposed key can be used, rather than restricting API access to authorized users.

---

## Option 2: Generate Separate API Keys for Each User

In this approach, instead of having one common API key, we can allow authorized dashboard users to generate their own API keys.

Each key will be mapped to a specific username, so we can identify who is using the API and revoke access individually.

**How it will work:**

1. The user logs into the dashboard using the existing authentication.
2. We add an API Key Management section to the dashboard.
3. The user can generate an API key, which will be mapped to their authenticated username.
4. On the backend, we maintain key details such as username, key ID, permissions, created date, expiry date, and status.
5. Whenever an API is called, the backend validates the provided key and checks the user's permissions.
6. Users or admins can revoke or regenerate keys whenever required.

**Advantages:**
- Every user will have their own API key.
- We can track API usage at the user level.
- If one user's key is compromised, we can revoke it without impacting others.
- We can control API access based on user permissions.
- This will also be useful if we want to provide API access to external applications in the future.

**Limitations:**
- Requires more development compared to the other options.
- We need to maintain API key records, expiry, revocation, and permissions.
- We will also need some management functionality on the dashboard.
- If a user's dashboard access is removed, their API key should also stop working. This needs to be checked on the backend.

One thing to consider here is that we don't necessarily need a new user-management database. We already have the user identity from our existing LDAP/Microsoft authentication.

We only need to maintain the API key details and their mapping to usernames. If we cannot make database changes, we can initially maintain this information in a secure, controlled file-based registry.

**My view:** This is a good option if we want proper user-level API key management. But it requires more development and maintenance, and it might be more than what we currently need.

---

## Option 3: Allow API Access Based on Dashboard Login (Recommended)

In this approach, we can use the existing dashboard authentication itself to control API access.

Instead of asking users to generate or manually provide API keys, the system will automatically issue a temporary access token after a successful login.

The same token can then be used for subsequent API calls.

**How it will work:**

1. The user logs into the Reporting Dashboard using the existing authentication mechanism.
2. The backend validates the login token and confirms that the user has dashboard access.
3. Once authenticated, the system generates a short-lived API access token.
4. The dashboard automatically includes this token in the request headers whenever it calls an API.
5. The backend validates the token, expiry, and required permissions before returning any data.
6. The token expires after a limited time and can be renewed as long as the user is still authorized.
7. If the user logs out or loses access, the API access should also be invalidated. For immediate revocation, we need server-side session validation or a similar mechanism.

For users who need to access an API directly through a URL, we can provide an option to generate a temporary signed URL after login.

For example, we can generate a link that is valid for only 5–15 minutes and only for the required API. This should be supported only where direct URL access is actually needed.

**Advantages:**
- We can reuse the authentication mechanism that is already available.
- No need to maintain a separate user database.
- Users don't need to manually generate or manage API keys.
- API access will be linked to the user's dashboard authorization.
- Temporary tokens reduce the risk of someone using an exposed credential for a long time.
- We don't need to introduce many changes in the dashboard UI.
- We can still introduce user-specific API keys later if required.

**Limitations:**
- We need to make sure the existing authentication is properly validated on the backend.
- Any external applications or scheduled jobs that run without a user login will need separate machine credentials.
- If we want immediate token revocation, we need a server-side mechanism to invalidate sessions or tokens.

**My view:** I think this is the most suitable approach for our current setup. We already have dashboard authentication, so instead of building another API key management system, we can extend the existing authentication to protect the APIs as well.

---

## Comparison

| Criteria | Option 1: Daily Key Rotation | Option 2: User API Keys | Option 3: Login-Based Access |
|---|---|---|---|
| Development effort | Low | High | Medium |
| Separate user database | Not required | Key registry needed | Not required |
| User identification | Not available per request | Yes | Yes |
| Linked to dashboard access | Only while retrieving key | Requires additional checks | Yes, with backend validation |
| Individual access revocation | No | Yes | Yes |
| Risk of key exposure | High when passed in URL | Depends on implementation | Lower with short-lived header tokens |
| External integrations | Possible, but rotation needed | Good support | Separate machine credentials needed |
| Maintenance | Medium | High | Low to medium |

## What I Suggest We Implement

I would prefer **Option 3**, mainly because we already have an authentication mechanism in the dashboard, and we should be able to reuse it rather than introducing a completely separate API key management process.

There are a few things we need to take care of during implementation.

**1. Fix the existing authentication validation**

Currently, we need to address how the `X-MSAL-ID-Token` header is being handled.

Just checking whether this header contains a value is not sufficient. We should properly validate the token or use a trusted server-side authenticated session.

Otherwise, someone could send a random value in this header and potentially bypass authentication.

**2. Add authentication checks for all protected APIs**

We should have a common authentication and authorization check on the backend.

This should apply to all protected endpoints, including chart APIs, export APIs, and any management-related APIs.

We should not depend only on whether the user can see or access something from the dashboard UI.

**3. Use temporary tokens instead of a common API key**

Once the user is authenticated, we can issue a temporary API token and use it in the request headers.

We also need to handle token expiry, renewal, logout, and access revocation properly.

For automated processes, we can use separate machine credentials so they don't depend on a user's dashboard session.

**4. Test the existing integrations**

Before removing the current shared API key mechanism, we need to identify where it is being used.

We should verify that existing scheduled jobs and integrations continue to work with the new authentication approach.

We also need to test scenarios like invalid tokens, expired tokens, unauthorized users, and revoked access.

## Final Recommendation

I think we can go with **Option 3 for now**.

Option 1 is simple, but even if we rotate the API key daily, anyone who gets the current key can still access the APIs. So it doesn't fully address the requirement.

Option 2 gives us more control, especially if we want every user to manage their own API keys. But it also adds more implementation and maintenance effort.

With Option 3, we can use the existing dashboard login to control API access. A user who is not authenticated or doesn't have the required dashboard permissions should not be able to obtain a valid API access token.

We should first fix the current authentication validation, then implement temporary login-based API tokens, and finally remove the shared API key dependency for dashboard users once everything has been tested.

This should address the current security requirement without adding unnecessary complexity. If we need user-specific API keys or external API access management in the future, we can extend this approach with Option 2.
