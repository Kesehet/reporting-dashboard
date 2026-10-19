"""Administrator-only PII key-rotation API.

All SQL work happens in ONE explicit transaction. Any failure calls rollback;
process termination before commit causes SQL Server to abort the open transaction.
Every changed row is backed up as authenticated ciphertext in a private file,
durably fsynced BEFORE committing, enabling a later explicit, conditional revert.
No DDL, new SQL tables, or SQL schema changes are performed.
"""
import hashlib
import hmac
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request

from helper.encryption_helper import (
    _atomic_write, _root, decrypt_string, encrypt_string, encrypted_key_id,
    get_keyring, is_versioned, key_metadata, key_rotation,
)

crypto_api = Blueprint("crypto_rotation", __name__, url_prefix="/crypto")
_TABLES = (
    ("Transactions", "tId", -1),
    ("Properties", "eCATrackingCode", ""),
)
_COLUMNS = ("PrimaryName", "PrimarySSN")
_active_lock = threading.Lock()
_active = False


def _now():
    return datetime.now(timezone.utc).isoformat()


def _state_file():
    return _root() / "migration-status.json"


def _write_status(value):
    _atomic_write(_state_file(), json.dumps(value, sort_keys=True))


def _status():
    path = _state_file()
    if not path.is_file():
        return {"state": "idle", "processed": 0, "updated": 0}
    return json.loads(path.read_text(encoding="utf-8"))


@crypto_api.before_request
def _admin_only():
    expected = os.environ.get("CRYPTO_ADMIN_TOKEN", "")
    actual = request.headers.get("X-Crypto-Admin-Token", "")
    if not expected or len(expected) < 32 or not hmac.compare_digest(actual, expected):
        return jsonify({"error": "Administrator authorization required"}), 403


@crypto_api.after_request
def _no_cache(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return response


def _connection():
    # Import lazily: no SQL connection on status/decrypt/key management.
    from DB import SQLConn
    sql = SQLConn()
    sql.connect()
    if sql.connection is None:
        raise RuntimeError("Database unavailable")
    return sql


def _column_lengths(cursor, table):
    cursor.execute(
        "SELECT COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH FROM "
        "[DigitalReport].INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? "
        "AND COLUMN_NAME IN ('PrimaryName', 'PrimarySSN')",
        (table,),
    )
    lengths = {name: limit for name, limit in cursor.fetchall()}
    if set(lengths) != set(_COLUMNS):
        raise ValueError("Required PII columns are missing in " + table)
    return lengths


def _rows(cursor, table, pk, initial, *, lock=False, page_size=200):
    """Read in PK order without holding a live resultset across writes."""
    last = initial
    hint = " WITH (UPDLOCK, HOLDLOCK)" if lock else ""
    while True:
        cursor.execute(
            "SELECT TOP (?) " + pk + ", PrimaryName, PrimarySSN "
            "FROM [DigitalReport].[dbo].[" + table + "]" + hint +
            " WHERE " + pk + " > ? ORDER BY " + pk,
            (page_size, last),
        )
        rows = cursor.fetchall()
        if not rows:
            return
        for row in rows:
            yield row
        last = rows[-1][0]


def _converted(value, current_id, ring, max_length, dry_run=False):
    if value is None or value == "":
        return value, False
    if not isinstance(value, str):
        raise ValueError("Unsupported PII value type")
    # Reject unsupported prefix instead of mistaking data for plaintext.
    plaintext = decrypt_string(value, ring=ring)
    if is_versioned(value) and encrypted_key_id(value) == current_id:
        return value, False
    if dry_run:
        candidate = encrypt_string(plaintext, ring=ring)
        if decrypt_string(candidate, ring=ring) != plaintext:
            raise RuntimeError("Authenticated encryption verification failed")
        if max_length != -1 and len(candidate) > max_length:
            if max_length < 36:
                raise ValueError("SQL column is too narrow for a file-backed reference")
            return "v2f:" + "0" * 32, True
        return candidate, True
    result = encrypt_string(plaintext, max_length=max_length, ring=ring)
    if decrypt_string(result, ring=ring) != plaintext:
        raise RuntimeError("Authenticated encryption verification failed")
    return result, True


def inspect_database():
    """Full dry-run: decrypt EVERY value and check column widths, no writes."""
    from helper.encryption_helper import verify_legacy_probe
    ring = get_keyring()
    current_id = ring.get("current_id")
    if not current_id:
        return {"ready": False, "reason": "Create an active GCM key first", "scanned": 0}
    sql = _connection()
    probe_checked = False
    result = {"ready": True, "scanned": 0, "values_to_rotate": 0,
              "already_current": 0, "failures": 0, "examples": []}
    try:
        cursor = sql.connection.cursor()
        for table, pk, initial in _TABLES:
            lengths = _column_lengths(cursor, table)
            for row in _rows(cursor, table, pk, initial):
                result["scanned"] += 1
                for column, value in zip(_COLUMNS, row[1:]):
                    if value in (None, ""):
                        continue
                    try:
                        if not is_versioned(value) and not probe_checked:
                            verify_legacy_probe()
                            probe_checked = True
                        next_value, changed = _converted(value, current_id, ring, lengths[column], dry_run=True)
                        capacity = lengths[column]
                        if capacity != -1 and len(next_value) > capacity:
                            raise ValueError("New ciphertext would exceed existing SQL column length")
                        if changed:
                            result["values_to_rotate"] += 1
                        else:
                            result["already_current"] += 1
                    except Exception as exc:
                        result["ready"] = False
                        result["failures"] += 1
                        if len(result["examples"]) < 10:
                            result["examples"].append({
                                "table": table, "column": column,
                                "error": str(exc).split(":")[0][:140],
                            })
        return result
    finally:
        sql.connection.rollback()  # dry run must never persist accidental writes
        sql.disconnect()


def _compare_update(cursor, table, pk, identity, before, after):
    if before == after:
        return
    # Optimistic guard: never overwrite a concurrent update, NULL included.
    cursor.execute(
        "UPDATE [DigitalReport].[dbo].[" + table + "] "
        "SET PrimaryName = ?, PrimarySSN = ? "
        "WHERE " + pk + " = ? "
        "AND (PrimaryName = ? OR (PrimaryName IS NULL AND ? IS NULL)) "
        "AND (PrimarySSN = ? OR (PrimarySSN IS NULL AND ? IS NULL))",
        (after[0], after[1], identity,
         before[0], before[0], before[1], before[1]),
    )
    if cursor.rowcount != 1:
        raise RuntimeError("Concurrent row modification detected; rolling back")


def _locked_run(run_id, operation):
    """OS-level exclusive migration lock across Flask workers."""
    # An O_EXCL lock prevents competing workers; never override a stale lock
    # automatically. Crash recovery uses SQL's transaction rollback.
    lock_path = _root() / "migration.lock"
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, run_id.encode("ascii"))
        os.fsync(fd)
        return operation()
    finally:
        os.close(fd)
        lock_path.unlink(missing_ok=True)


def _migrate(run_id):
    status = {"state": "running", "run_id": run_id, "started_at": _now(),
              "processed": 0, "updated": 0}
    _write_status(status)
    sql = None
    committed = False
    try:
        # Recheck the entire dataset immediately before writing.
        preflight = inspect_database()
        if not preflight.get("ready"):
            raise RuntimeError("Preflight failed; no data was changed")
        sql = _connection()
        cursor = sql.connection.cursor()
        ring = get_keyring()
        current_id = ring["current_id"]
        probe_checked = False
        created_external = set()
        backup_path = _root() / "backups" / (run_id + ".jsonl")
        backup_path.parent.mkdir(mode=0o700, exist_ok=True)
        digest = hashlib.sha256()
        with open(backup_path, "x", encoding="utf-8") as backup:
            if os.name != "nt":
                os.chmod(backup_path, 0o600)
            for table, pk, initial in _TABLES:
                lengths = _column_lengths(cursor, table)
                for row in _rows(cursor, table, pk, initial, lock=True):
                    identity = row[0]
                    before = [row[1], row[2]]
                    after = []
                    for column, old in zip(_COLUMNS, before):
                        if old not in (None, "") and not is_versioned(old) and not probe_checked:
                            from helper.encryption_helper import verify_legacy_probe
                            verify_legacy_probe()
                            probe_checked = True
                        result, _ = _converted(old, current_id, ring, lengths[column])
                        cap = lengths[column]
                        if cap != -1 and result is not None and len(result) > cap:
                            raise RuntimeError("Column capacity changed since preflight")
                        after.append(result)
                        if isinstance(result, str) and result.startswith("v2f:") and result != old:
                            created_external.add(result[4:])
                    if after != before:
                        original = {"table": table, "pk": pk, "id": identity,
                                    "before": before, "after": after}
                        sealed = encrypt_string(json.dumps(original, separators=(",", ":")))
                        line = sealed + "\n"
                        backup.write(line)
                        digest.update(line.encode("utf-8"))
                        _compare_update(cursor, table, pk, identity, before, after)
                        status["updated"] += 1
                    status["processed"] += 1
                    if status["processed"] % 200 == 0:
                        _write_status(status)
            backup.flush()
            os.fsync(backup.fileno())
        # Durable snapshot and manifest MUST exist before database commit.
        status.update({"state": "committing", "backup_sha256": digest.hexdigest(),
                       "backup_rows": status["updated"], "backup_run_id": run_id})
        _write_status(status)
        sql.connection.commit()
        committed = True
        status.update({"state": "completed", "finished_at": _now()})
        _write_status(status)
    except Exception:
        if sql is not None and not committed:
            sql.connection.rollback()
            for file_id in locals().get("created_external", set()):
                (_root() / "values" / (file_id + ".enc")).unlink(missing_ok=True)
        status.update({"state": "reconciliation_required" if committed else "failed",
                       "finished_at": _now(),
                       "error": "Commit outcome requires review" if committed else "Migration aborted; SQL transaction rolled back"})
        _write_status(status)
    finally:
        if sql is not None:
            sql.disconnect()


def _rollback(run_id):
    status = _status()
    if status.get("run_id") != run_id or status.get("state") not in ("completed", "committing"):
        raise ValueError("No completed or uncertain migration with this run id")
    backup_path = _root() / "backups" / (run_id + ".jsonl")
    if not backup_path.is_file():
        raise ValueError("Recovery snapshot missing; refusing to proceed")
    encoded_lines = backup_path.read_bytes()
    if hashlib.sha256(encoded_lines).hexdigest() != status.get("backup_sha256"):
        raise ValueError("Recovery snapshot checksum mismatch")
    lines = encoded_lines.decode("utf-8").splitlines()
    if len(lines) != status.get("backup_rows"):
        raise ValueError("Recovery snapshot is incomplete")
    sql = _connection()
    try:
        cursor = sql.connection.cursor()
        for line in lines:
            item = json.loads(decrypt_string(line))
            allowed = {name: pk for name, pk, _ in _TABLES}
            if item.get("pk") != allowed.get(item.get("table")):
                raise ValueError("Invalid recovery snapshot table")
            _compare_update(cursor, item["table"], item["pk"], item["id"],
                            item["after"], item["before"])
        sql.connection.commit()
        status.update({"state": "rolled_back", "finished_at": _now()})
        _write_status(status)
    except Exception:
        sql.connection.rollback()
        raise
    finally:
        sql.disconnect()


def _async_runner(run_id, action):
    global _active
    try:
        _locked_run(run_id, action)
    except Exception:
        old = _status()
        old.update({"state": "reconciliation_required",
                    "error": "Migration or recovery operation needs investigation; no overwrite attempted"})
        _write_status(old)
    finally:
        with _active_lock:
            _active = False


def _launch(run_id, action):
    global _active
    with _active_lock:
        if _active or (_root() / "migration.lock").exists():
            return False
        _active = True
    threading.Thread(target=_async_runner, args=(run_id, action),
                     daemon=True, name="pii-rotation").start()
    return True


@crypto_api.get("/status")
def status_api():
    job = _status()
    # Never claim success for a crashed or unknown post-commit state.
    if job.get("state") in ("running", "committing") and not _active and not (_root() / "migration.lock").exists():
        job["state"] = "reconciliation_required"
    return jsonify({"keyring": key_metadata(), "job": job})


@crypto_api.post("/keys/rotate")
def rotate_key_api():
    data = request.get_json(silent=True) or {}
    if data.get("confirm") != "CREATE_GCM_KEY" or _active:
        return jsonify({"error": "Explicit confirmation required or migration active"}), 409
    try:
        key_id = key_rotation()
        return jsonify({"key_id": key_id}), 201
    except Exception:
        return jsonify({"error": "Failed to store key safely"}), 500


@crypto_api.post("/decrypt")
def decrypt_api():
    data = request.get_json(silent=True) or {}
    value = data.get("value")
    if not isinstance(value, str) or not (0 < len(value) <= 20000):
        return jsonify({"error": "Ciphertext must be 1–20000 characters"}), 400
    try:
        return jsonify({"plaintext": decrypt_string(value)})
    except Exception:
        return jsonify({"error": "Cannot decrypt with an available key and supported mode"}), 422


@crypto_api.post("/preflight")
def preflight_api():
    if _active:
        return jsonify({"error": "Migration already running"}), 409
    try:
        report = inspect_database()
        return jsonify(report), 200
    except Exception:
        return jsonify({"ready": False, "error": "Preflight failed; check DB and key configuration"}), 503


@crypto_api.post("/start")
def start_api():
    data = request.get_json(silent=True) or {}
    if data.get("confirm") != "MIGRATE_PII" or get_keyring().get("current_id") is None:
        return jsonify({"error": "Confirmation and an active GCM key are required"}), 409
    if _status().get("state") in ("running", "committing", "reconciliation_required"):
        return jsonify({"error": "Previous operation must be reconciled first"}), 409
    run_id = uuid.uuid4().hex
    if not _launch(run_id, lambda: _migrate(run_id)):
        return jsonify({"error": "Another migration is running"}), 409
    return jsonify({"run_id": run_id, "state": "starting"}), 202


@crypto_api.post("/rollback")
def rollback_api():
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or len(run_id) != 32 or data.get("confirm") != "RESTORE_ORIGINAL":
        return jsonify({"error": "Run id and explicit confirmation required"}), 400
    if not _launch(run_id, lambda: _rollback(run_id)):
        return jsonify({"error": "Another migration is running"}), 409
    return jsonify({"state": "starting", "run_id": run_id}), 202
