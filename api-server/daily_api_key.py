"""Stateless daily API keys derived from a private secret and the UTC date."""
import hashlib
import hmac
from datetime import datetime, timezone


def utc_today():
    return datetime.now(timezone.utc).date()


def make_daily_api_key(secret, day=None):
    """The same secret and UTC day produce exactly the same key on every server."""
    if not isinstance(secret, str) or not secret:
        return None
    stamp = (day or utc_today()).strftime('%Y%m%d')
    message = f'reporting-dashboard:daily-api-key:v1:{stamp}'.encode('ascii')
    signature = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).hexdigest()
    return f'ak1.{stamp}.{signature}'


def valid_daily_api_key(value, secret, day=None):
    expected = make_daily_api_key(secret, day)
    return bool(expected and isinstance(value, str) and hmac.compare_digest(value, expected))
