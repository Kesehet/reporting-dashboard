# Business String Decryption

Open **Tools → Business String Decryption** on the reporting dashboard sidebar.

## Server configuration

The tool uses server-side keys from the encryption keyring, including existing `enc.key` and `old_enc.key` files when present. Supported AES keys are 16, 24, or 32 bytes. Key material must never be configured through `REACT_APP_*` variables.

The endpoint requires no separate tool access token. The frontend uses `REACT_APP_API_SERVER_BASE_URL` if configured, otherwise `http://localhost:5000` in development and `/api` in production.

**Deployment warning:** There is no application session-auth middleware. Anyone able to reach the API can submit ciphertext and retrieve decrypted values. Restrict network exposure through the deployment infrastructure and use HTTPS.

## How to use

Paste an encrypted value and click **Decrypt string**. **Clear all** removes the input, result and status from the UI. The endpoint is POST-only (`/tools/decrypt`), returns JSON, and has `no-store` caching headers. The app does not log the values, place them into URL query strings, or save them to browser storage.

Status codes: 400 malformed request; 413 oversized input; 422 invalid, unsupported or tampered ciphertext; 503 unavailable key files.

## Important legacy limitation

An earlier AES-GCM helper did not save its nonce or authentication tag; ciphertext written by that version cannot be recovered from the key alone. Current `v2:` values include the nonce and authentication tag. The endpoint also supports verified historical GCM envelopes and explicitly configured legacy AES-ECB/PKCS7 values when the matching key is available. Legacy ECB data has no authentication, so verify its format against a known sample before relying on the result. Recover unrecoverable values from backups or original sources. Check column lengths before bulk migration because versioned ciphertext may be longer.

Neither key file is auto-generated during imports or startup, preventing accidental loss of decryption continuity.

## Tests and CI

- `python -m unittest discover -s tests/decryption -p 'test_decryption.py' -v`
- `npm run test:nocov -- --runInBand --testPathPattern=Decryption`
- `.github/workflows/decryption.yml` runs backend tests, frontend tests, and production build.
