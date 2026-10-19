"""Operator-only string decryption route.

The existing reporting dashboard has no active session-auth middleware. This
sensitive endpoint therefore requires a separate, long random access token.
It never accepts an encryption key from the browser.
"""
import hmac
import os

from flask import Blueprint, jsonify, request

from helper.encryption_helper import encrypt_decrypt_string

decrypt_tools = Blueprint("decrypt_tools", __name__)
MAX_CIPHERTEXT_LENGTH = 65536


@decrypt_tools.after_request
def prevent_sensitive_caching(response):
    response.headers["Cache-Control"] = "no-store, no-cache, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@decrypt_tools.route("/tools/decrypt", methods=["POST"])
def decrypt_string():
    expected = os.getenv("DECRYPT_TOOL_API_KEY", "")
    if len(expected) < 32:
        return jsonify(error="Decryption tool is not configured."), 503

    supplied = request.headers.get("X-Decrypt-Access-Key", "")
    if not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify(error="Access denied."), 403

    # Only permit same-origin requests, or explicitly configured dashboard
    # origins. This also protects installations with permissive global CORS.
    origin = request.headers.get("Origin")
    allowed = {
        item.strip().rstrip("/")
        for item in os.getenv("DECRYPT_TOOL_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    }
    if origin and origin.rstrip("/") not in allowed | {request.host_url.rstrip("/")}:
        return jsonify(error="Origin not allowed."), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="A JSON object is required."), 400

    value = data.get("ciphertext")
    if not isinstance(value, str) or not value.strip():
        return jsonify(error="An encrypted string is required."), 400
    if len(value) > MAX_CIPHERTEXT_LENGTH:
        return jsonify(error="Encrypted string is too large."), 413

    try:
        plaintext = encrypt_decrypt_string(value.strip(), mode="decrypt")
    except (ValueError, UnicodeDecodeError):
        # Do not echo submitted text, key material, stack traces or primitives.
        return jsonify(error="Decryption failed. Check the value and key version."), 422
    except OSError:
        return jsonify(error="Decryption key files are not available."), 503

    return jsonify(plaintext=plaintext), 200
