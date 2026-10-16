
from datetime import datetime
import traceback
import threading
import time
import json
import uuid


# --- In-process concurrency gate (global to this module) ---
_MAX_WAIT_SECONDS = 30
_INFLIGHT = {}  # key -> {"event": threading.Event(), "started_at": float, "owner": str}
_INFLIGHT_LOCK = threading.Lock()


def _normalize_params_for_key(params: dict) -> str:
    """
    Produces a deterministic JSON string for request params to be used in the key.
    Falls back to stringifying non-serializable values.
    """
    if params is None:
        params = {}
    try:
        return json.dumps(params, sort_keys=True, separators=(",", ":"), default=str)
    except TypeError:
        # Fallback: stringify values
        safe = {k: str(v) for k, v in params.items()}
        return json.dumps(safe, sort_keys=True, separators=(",", ":"))


def _chart_key(name: str, start_date: str, end_date: str, params: dict) -> str:
    """
    Unique key for the requested chart workload based on name + date range + params.
    """
    return f"{name}|{start_date}|{end_date}|{_normalize_params_for_key(params)}"


def _acquire_or_wait_for_slot(key: str):
    """
    Returns a tuple (role, event_obj) where:
      - role == "owner": caller is responsible for computing and must signal completion via event.
      - role == "waiter_completed": a prior owner has completed; cache should be available.
      - role == "waiter_failed_or_timeout": prior owner likely failed; cache might be missing.

    Behavior:
      * If no in-flight entry exists, becomes owner immediately.
      * If an in-flight entry exists, waits until either:
          - the current owner finishes (event set) -> return waiter_completed
          - or 30s elapse since that owner's start -> attempt to supersede and become the new owner
            (only if the same entry is still current). If another request already superseded, wait
            for that new owner to finish (bounded wait).
    """
    while True:
        # Snapshot current entry without holding the lock for the wait.
        with _INFLIGHT_LOCK:
            entry = _INFLIGHT.get(key)
            if entry is None:
                # No one is working on this key; become owner
                ev = threading.Event()
                _INFLIGHT[key] = {
                    "event": ev,
                    "started_at": time.monotonic(),
                    "owner": uuid.uuid4().hex,
                }
                return "owner", ev

            ev = entry["event"]
            started_at = entry["started_at"]

        # Compute deadline relative to the original owner's start
        deadline = started_at + _MAX_WAIT_SECONDS
        now = time.monotonic()
        if now < deadline:
            # Wait until the current owner's deadline
            ev.wait(deadline - now)
            if ev.is_set():
                # Prior owner finished; cache should now be available
                return "waiter_completed", None
            # Otherwise, deadline reached; attempt to supersede
        # Try to supersede if the same entry is still current
        with _INFLIGHT_LOCK:
            current = _INFLIGHT.get(key)
            if current is entry and not current["event"].is_set():
                # Supersede the old in-flight owner
                new_ev = threading.Event()
                _INFLIGHT[key] = {
                    "event": new_ev,
                    "started_at": time.monotonic(),
                    "owner": uuid.uuid4().hex,
                }
                return "owner", new_ev

            # If the current entry changed:
            #   - Either the previous owner finished or another request already superseded.
            # Wait for the new/current owner to finish (bounded wait), then try to use cache.
            if current is None:
                # Cleared by owner after completion; treat as completed.
                return "waiter_completed", None

            # Wait bounded time for the new/current owner to finish
            current["event"].wait(_MAX_WAIT_SECONDS)
            if current["event"].is_set():
                return "waiter_completed", None
            # If still not set after another bounded wait, treat as failed/timeout and loop again.
            # The loop will either supersede next time (if still the same entry) or continue waiting.
            # To avoid indefinite spin, allow one propagation of failure condition:
            return "waiter_failed_or_timeout", None
