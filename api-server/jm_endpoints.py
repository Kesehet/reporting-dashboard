"""Build Journey Manager URLs from one configuration, without duplicating path segments.

JM_BASE_URL may be the server origin, a deployment prefix, or a complete Fluent
API endpoint. The legacy /secure/rest/fluentapi route remains the default; the
/manager variant is honored only when explicitly included in configuration.
"""
import os
from urllib.parse import urlsplit, urlunsplit

from config import get_env_value

_FLUENT_PATH = "/secure/rest/fluentapi"
_MANAGER_FLUENT_PATH = "/manager" + _FLUENT_PATH


def _configured_url(base_url=None):
    raw = base_url if base_url is not None else (
        get_env_value("JM_BASE_URL") or os.environ.get("JM_BASE_URL")
    )
    if not raw or not str(raw).strip():
        raise ValueError("JM_BASE_URL is not configured")
    parsed = urlsplit(str(raw).strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("JM_BASE_URL must be an absolute http(s) URL")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("JM_BASE_URL must not contain credentials, query or fragment")
    return parsed, parsed.path.rstrip("/")


def jm_fluent_base_url(base_url=None):
    """Return the complete Fluent API base, preserving an explicit /manager."""
    parsed, path = _configured_url(base_url)
    if not path.endswith(_FLUENT_PATH):
        path += _FLUENT_PATH
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def jm_workspaces_url(base_url=None):
    """Build the separate workspaces API against the server/deployment root."""
    parsed, path = _configured_url(base_url)
    if path.endswith(_MANAGER_FLUENT_PATH):
        path = path[:-len(_MANAGER_FLUENT_PATH)]
    elif path.endswith(_FLUENT_PATH):
        path = path[:-len(_FLUENT_PATH)]
    elif path.endswith("/manager"):
        path = path[:-len("/manager")]
    return urlunsplit((parsed.scheme, parsed.netloc, path + "/workspaces", "", ""))
