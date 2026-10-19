# Production key rotation and PII migration

## Before migrating
An older AES-GCM helper did not save nonces or authentication tags. Data written
by that version cannot be decrypted using the key alone. Do not attempt to
migrate those values without recovering the original plaintext.

The original production ECB routine was not present in this repository's
history, so confirm its cipher, padding, and encoding using a known non-PII
test vector before enabling legacy migration.

## Configuration and retention

Set these only on the backend server (never as `REACT_APP_*` variables):
- CRYPTO_STATE_DIR: absolute persistent private directory outside the web root.
  Back up the entire directory, not just the keyring file.
- CRYPTO_ADMIN_TOKEN: at least 32 random characters. Must be entered by a
  trusted operator in the dashboard UI, over HTTPS. It is not stored in the browser.
- CRYPTO_LEGACY_MODE=AES_ECB_PKCS7: set only after verifying an original ECB/PKCS7 sample.
- CRYPTO_LEGACY_SAMPLE_CIPHERTEXT: a known original ECB test ciphertext.
- CRYPTO_LEGACY_SAMPLE_SHA256: SHA-256 hex of its known original plaintext.
- ENCRYPTION_KEY: existing legacy key from environment or .env.

On access, historical AES keys are automatically archived from ENCRYPTION_KEY,
enc.key, old_enc.key, and every .key file in CRYPTO_STATE_DIR/import. Valid
formats are base64 and explicit hex: or raw: prefixes. Do not delete any keys.
No key is generated automatically during module import.

CRYPTO_STATE_DIR contains:
- keyring.json: every historical key, with stable fingerprints and current ID
- keyring-history/*.json: immutable snapshots of previous keyring states
- values/*.enc: AES-GCM-protected files for encrypted values that exceed the
  existing SQL column length
- backups/RUN_ID.jsonl: authenticated snapshots of original SQL ciphertext
- migration-status.json and migration.lock: operation journal/coordination

Keys and protected files must be writable only by the backend service account.
Never put secrets, backups or PII in Git, public directories, CI artifacts,
browser local storage, or ordinary logs.

New data uses AES-GCM with a fresh nonce, authentication tag, and version/key
ID. SQL columns store either a self-contained v2 envelope or a short v2f file
reference, depending on the existing column's maximum length. If a v2f file
is lost, the corresponding value is unrecoverable even with its encryption key.
SQL backups and filesystem backups must be coordinated.

## Production rollout

1. Take and verify restorable backups of SQL, .env, both old key files and the
   entire crypto state directory. Check free disk space.
2. Pause CSV ingestion, ETL and all writers modifying PrimaryName/PrimarySSN.
   Coordinate an outage window because migration uses one SQL transaction,
   keeping row locks until commit.
3. Verify original ECB test vector and import all known historical keys.
   Unknown formats or keys must stop migration.
4. Deploy first against staging SQL and a private copy of the crypto files.
5. Open Crypto & Key Rotation in the dashboard. Authenticate with admin token.
6. Explicitly create/activate a new GCM key. This action keeps the old keys and
   does not bulk-modify existing SQL ciphertext.
7. Run read-only preflight. It verifies all existing ciphertext can decrypt,
   checks GCM round trips, SQL column lengths, and file-reference capacity.
   Any failure prevents a production migration.
8. Enter MIGRATE_PII and start. It repeats the preflight then processes
   Transactions and Properties in one SQL transaction. The encrypted recovery
   journal is synced to disk before SQL commit.
9. Verify completed status and representative reports. Retain recovery
   journal, historical keys and file-backed values; only then resume writers.

This migration does not change SQL tables or columns.

## Rollback and crash recovery

- A SQL write failure or verification error before commit rolls back the whole
  transaction automatically. Process termination closes the SQL connection and
  SQL Server rolls back the uncommitted transaction.
- If status could not be updated after commit, the operation is marked
  reconciliation_required. Filesystem and SQL commits are not atomic together.
  Investigate; do not assume the database has been restored.
- For a completed migration, enter RESTORE_ORIGINAL and the run ID. Recovery
  authenticates the backup and checks current ciphertext equals the expected
  post-migration value before restoring the original field contents. If a
  concurrent write changed even one value, the entire restore is aborted
  instead of blindly clobbering later updates.
- An OS crash can leave migration.lock. Confirm no active writer and reconcile
  the SQL transaction and snapshot before manually clearing a stale lock.
- Do not expect reconstruction of missing historical keys or missing old GCM
  nonces/tags. AES-ECB has no integrity authentication even when padding checks
  succeed, so use known data samples and independent backups.

## Regression commands

python -m pip install pycryptodome Flask python-dotenv

python -m unittest discover -s tests -p test_crypto_rotation.py -v

npm test -- --watchAll=false --runInBand --coverage=false --testPathPattern=CryptoRotationTab.test.js

GitHub Actions also compiles changed Python modules and builds the dashboard.
The existing main application has unrelated ESLint warnings: this feature's
CI compilation checks may use CI=false for the build step until that existing
lint backlog is addressed; the new unit tests still execute with CI=true.
