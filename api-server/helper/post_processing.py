"""Authenticated manual post-processing runs and their durable, sanitized history."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from threading import Lock, Thread

from flask import Blueprint, current_app, jsonify, request

from authentication import unauthorized, verify_token
from csvLoader import update_JMExtracts
from DB import SQLConn, Transaction
from post_process import ensure_properties_table, process_dds_amounts

post_processing = Blueprint("post_processing", __name__, url_prefix="/post-processing")
_run_lock = Lock()
logger = logging.getLogger(__name__)


def _dds(sql, txn, report_error):
    ensure_properties_table(txn)
    process_dds_amounts(sql, txn, report_error=report_error)


_TASKS = {"dds-amount": _dds, "jm-extract": update_JMExtracts}


def _now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _history(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY, task TEXT NOT NULL, status TEXT NOT NULL,
                started_at TEXT NOT NULL, finished_at TEXT, errors TEXT NOT NULL DEFAULT '{}'
            )
        """)
        yield db


def _path():
    return Path(current_app.config.get("POST_PROCESSING_HISTORY", "post-processing-history.sqlite3"))


def _interrupt_unfinished(db):
    rows = db.execute("SELECT id, errors FROM runs WHERE status = 'running'").fetchall()
    for row in rows:
        errors = json.loads(row["errors"])
        errors["API service stopped during the run."] = 1
        db.execute(
            "UPDATE runs SET status = 'interrupted', finished_at = ?, errors = ? WHERE id = ?",
            (_now(), json.dumps(errors), row["id"]),
        )


def _run(path, run_id, task):
    errors = {}

    def report_error(message):
        errors[message] = errors.get(message, 0) + 1
        with _history(path) as db:
            db.execute("UPDATE runs SET errors = ? WHERE id = ?", (json.dumps(errors), run_id))

    status = "failed"
    try:
        sql = SQLConn()
        try:
            sql.connect()
            if not sql.connection:
                report_error("Reporting database connection unavailable.")
            else:
                _TASKS[task](sql, Transaction(sql), report_error=report_error)
                status = "completed_with_errors" if errors else "completed"
        finally:
            sql.disconnect()
    except Exception as exc:
        logger.error("Post-processing run %s (%s) failed: %s", run_id, task, type(exc).__name__)
        status = "failed"
        report_error("Task stopped unexpectedly. Check the API service logs.")
    finally:
        try:
            with _history(path) as db:
                db.execute(
                    "UPDATE runs SET status = ?, finished_at = ? WHERE id = ?",
                    (status, _now(), run_id),
                )
        finally:
            _run_lock.release()


@post_processing.before_request
def require_session():
    if not verify_token(request.headers.get("X-MSAL-ID-Token") or request.headers.get("Authorization")):
        return unauthorized()


@post_processing.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@post_processing.get("/runs")
def list_runs():
    with _history(_path()) as db:
        if _run_lock.acquire(blocking=False):
            try:
                _interrupt_unfinished(db)
                db.commit()
            finally:
                _run_lock.release()
        rows = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify({"runs": [dict(row, errors=json.loads(row["errors"])) for row in rows]})


@post_processing.post("/tasks/<task>/runs")
def start_run(task):
    if task not in _TASKS:
        return jsonify({"error": "Unknown post-processing task."}), 404
    if not _run_lock.acquire(blocking=False):
        return jsonify({"error": "A manual post-processing task is already running."}), 409

    try:
        path = _path().resolve()
        with _history(path) as db:
            _interrupt_unfinished(db)
            run_id = db.execute(
                "INSERT INTO runs (task, status, started_at) VALUES (?, 'running', ?)",
                (task, _now()),
            ).lastrowid
        Thread(target=_run, args=(path, run_id, task), daemon=True).start()
    except Exception:
        _run_lock.release()
        raise
    return jsonify({"id": run_id}), 202
