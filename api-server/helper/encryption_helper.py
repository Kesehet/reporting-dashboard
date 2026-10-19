"""Encryption at rest for PII. Keep key files on the server, never in the UI.

v2 stores the random AES-GCM nonce and authentication tag with the ciphertext.
Older unversioned values written by this project's former AES-GCM helper omitted
both nonce and tag; they cannot be recovered from the ciphertext and key alone.
"""
import base64
import binascii
import os
import secrets

from Crypto.Cipher import AES

CURRENT_KEY_FILE = "enc.key"
OLD_KEY_FILE = "old_enc.key"
PREFIX = "v2:"
NONCE_SIZE = 12
TAG_SIZE = 16


def load_key(key_file=CURRENT_KEY_FILE):
    """Load a base64-encoded AES-256 key from a server-side file."""
    with open(key_file, "r", encoding="ascii") as handle:
        data = handle.read().strip()
    try:
        key = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid key file") from exc
    if len(key) != 32:
        raise ValueError("Encryption key must contain 32 bytes")
    return key


def save_key(key_bytes, key_file):
    if len(key_bytes) != 32:
        raise ValueError("Encryption key must contain 32 bytes")
    # Only used for explicitly requested key provisioning/rotation.
    with open(key_file, "w", encoding="ascii") as handle:
        handle.write(base64.b64encode(key_bytes).decode("ascii"))


def key_rotation():
    """Retain the previous key for decrypting v2 values during rotation."""
    if os.path.exists(CURRENT_KEY_FILE):
        with open(CURRENT_KEY_FILE, "rb") as source:
            current_key = source.read()
        with open(OLD_KEY_FILE, "wb") as target:
            target.write(current_key)
    save_key(secrets.token_bytes(32), CURRENT_KEY_FILE)


def _decrypt_with_key(encoded_value, key):
    if not isinstance(encoded_value, str) or not encoded_value.startswith(PREFIX):
        raise ValueError("Unsupported ciphertext format")
    try:
        raw = base64.b64decode(encoded_value[len(PREFIX):], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid ciphertext encoding") from exc

    if len(raw) < NONCE_SIZE + TAG_SIZE:
        raise ValueError("Invalid ciphertext length")
    nonce = raw[:NONCE_SIZE]
    tag = raw[NONCE_SIZE:NONCE_SIZE + TAG_SIZE]
    ciphertext = raw[NONCE_SIZE + TAG_SIZE:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


def is_encrypted(value):
    """Conservatively protect stored ciphertext from a second encryption pass.

    The v2 prefix identifies new ciphertext. Legacy base64 AES-block-sized
    values are treated as encrypted *without* claiming they can be decrypted.
    This is intentional: the old format has no nonce or authentication tag.
    """
    if not isinstance(value, str) or not value:
        return False
    if value.startswith(PREFIX):
        return True
    try:
        decoded = base64.b64decode(value, validate=True)
        return bool(decoded) and len(decoded) % AES.block_size == 0
    except (ValueError, binascii.Error):
        return False


def encrypt_decrypt_string(input_string, mode="encrypt"):
    if not isinstance(input_string, str):
        raise ValueError("Input must be a string")

    if mode == "encrypt":
        key = load_key(CURRENT_KEY_FILE)
        cipher = AES.new(key, AES.MODE_GCM, nonce=secrets.token_bytes(NONCE_SIZE))
        ciphertext, tag = cipher.encrypt_and_digest(input_string.encode("utf-8"))
        return PREFIX + base64.b64encode(cipher.nonce + tag + ciphertext).decode("ascii")

    if mode == "decrypt":
        if not input_string.startswith(PREFIX):
            raise ValueError("Unsupported legacy ciphertext (missing AES-GCM nonce/tag)")
        if not any(os.path.exists(p) for p in (CURRENT_KEY_FILE, OLD_KEY_FILE)):
            raise FileNotFoundError("No server-side encryption key is available")
        for key_file in (CURRENT_KEY_FILE, OLD_KEY_FILE):
            if not os.path.exists(key_file):
                continue
            key = load_key(key_file)
            try:
                return _decrypt_with_key(input_string, key)
            except (ValueError, UnicodeDecodeError):
                continue
        raise ValueError("Unable to decrypt with current or previous key")

    raise ValueError("Mode must be 'encrypt' or 'decrypt'")
