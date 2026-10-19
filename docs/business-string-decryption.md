# Business String Decryption

Open **Tools → Business String Decryption** on the reporting dashboard sidebar.

## Server configuration

This restricted operation uses the existing server-side `enc.key` (32-byte AES key encoded as base64); `old_enc.key` is optional for rotation. Neither key leaves the server. Do **not** use a `REACT_APP_*` variable for key material.

Set `DECRYPT_TOOL_API_KEY` to a random, private string of **at least 32 characters**, distinct from the AES key. It is an operator authorization token, not a decryption key. If unset, the endpoint is disabled (HTTP 503).

For a separate frontend origin, set `DECRYPT_TOOL_ALLOWED_ORIGINS` to a comma-separated list of trusted origins such as `http://localhost:3000`. Same-origin calls work without this setting. The frontend uses `REACT_APP_API_SERVER_BASE_URL` if configured, otherwise `http://localhost:5000` in development and `/api` in production.

Run over HTTPS, and limit operator access using your organization's controls. The dashboard currently has no active authentication middleware, so this endpoint requires its own token.

## How to use

Enter the tool access token, paste a `v2:...` ciphertext, click **Decrypt string**, and copy the result when authorized. **Clear all** removes the token, input, result and status from the UI. The endpoint is POST-only (`/tools/decrypt`), returns JSON, and has `no-store` caching headers. The app does not log the values, place them into URL query strings, or save them to browser storage.

Status codes: 403 bad token/unauthorized origin; 400 malformed request; 413 oversized input; 422 invalid, unsupported or tampered ciphertext; 503 missing key/configuration.

## Important legacy limitation

The former encryption helper used AES-GCM **without saving the random nonce or authentication tag**. This makes existing unversioned ciphertext from that helper generally unrecoverable, even with its key. The versioned `v2:` envelope stores a random 12-byte nonce + 16-byte authentication tag + encrypted UTF-8 bytes, encoded as base64. The decrypt endpoint accepts only authenticated v2 values. The existing ETL guard conservatively recognizes legacy-looking ciphertext so it is not accidentally encrypted again. Recover legacy plaintext from backups or original input sources if available. Verify column lengths before bulk-encrypting with v2 because its envelope is longer.

Neither key file is auto-generated during imports or startup, preventing accidental loss of decryption continuity.

## Tests and CI

- `python -m unittest discover -s tests/decryption -p 'test_decryption.py' -v`
- `npm run test:nocov -- --runInBand --testPathPattern=Decryption`
- `.github/workflows/decryption.yml` runs backend tests, frontend tests, and production build.
