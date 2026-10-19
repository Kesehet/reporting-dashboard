"""Versioned, authenticated field encryption and durable file-backed historical keys.

No key is generated during import. Existing production key files and ENCRYPTION_KEY
are imported, never deleted, and never overwritten. State is outside the web root.
Unversioned ciphertext is decrypted ONLY with an explicitly configured legacy mode.
"""
import base64
import binascii
import hashlib
import json
import os
import secrets
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from Crypto.Cipher import AES

_VERSION = "v2"
_NONCE_SIZE = 12
_TAG_SIZE = 16
_LOCK = RLock()
CURRENT_KEY_FILE = "enc.key"
OLD_KEY_FILE = "old_enc.key"


def _root():
    configured = os.environ.get("CRYPTO_STATE_DIR")
    path = Path(configured).expanduser() if configured else Path.home() / ".reporting-dashboard-crypto"
    if not path.is_absolute():
        raise ValueError("CRYPTO_STATE_DIR must be an absolute, private directory")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.chmod(path, 0o700)
    return path


def _atomic_write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".crypto-", dir=str(path.parent))
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
        if hasattr(os, "O_DIRECTORY"):
            dfd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _decode_key(value):
    value = value.strip()
    if value.startswith("hex:"):
        raw = bytes.fromhex(value[4:])
    elif value.startswith("raw:"):
        raw = value[4:].encode("utf-8")
    else:
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            raw = value.encode("utf-8")
    if len(raw) not in (16, 24, 32):
        raise ValueError("Legacy key must be a 16-, 24-, or 32-byte AES key")
    return raw


def _key_id(raw):
    return hashlib.sha256(raw).hexdigest()[:20]


def _load_ring():
    path = _root() / "keyring.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or not isinstance(data.get("keys"), list):
            raise ValueError("Invalid keyring format; refusing to create a replacement")
    else:
        data = {"version": 1, "current_id": None, "keys": []}
    return data


def _save_ring(ring):
    _atomic_write(_root() / "keyring.json", json.dumps(ring, sort_keys=True, indent=2))


def _insert(ring, raw, algorithm, source):
    kid = _key_id(raw)
    for existing in ring["keys"]:
        if existing["id"] == kid:
            if base64.b64decode(existing["material"]) != raw:
                raise ValueError("Key fingerprint collision")
            return False
    ring["keys"].append({
        "id": kid, "algorithm": algorithm,
        "material": base64.b64encode(raw).decode("ascii"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
    })
    return True


def _legacy_env():
    value = os.getenv("ENCRYPTION_KEY")
    if value:
        return value
    # Compatible with this repository's non-exported .env reading pattern.
    from config import get_env_value
    return get_env_value("ENCRYPTION_KEY")


@contextmanager
def _ring_file_lock():
    """Interprocess lock across Flask workers; prevents losing historic keys."""
    path = _root() / "keyring.lock"
    with open(path, "a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _sync_ring():
    ring = _load_ring()
    changed = False
    legacy_sources = []
    env_key = _legacy_env()
    if env_key:
        legacy_sources.append(("env", env_key))
    for name in (CURRENT_KEY_FILE, OLD_KEY_FILE):
        path = Path(name)
        if path.is_file():
            legacy_sources.append((name, path.read_text(encoding="utf-8")))
    archive = _root() / "import"
    if archive.is_dir():
        for path in sorted(archive.glob("*.key")):
            legacy_sources.append(("historical-file", path.read_text(encoding="utf-8")))
    for source, value in legacy_sources:
        changed |= _insert(ring, _decode_key(value), "AES_ECB_PKCS7", source)
    if changed:
        _save_ring(ring)
    return ring


def get_keyring():
    """Import every available historical key before returning a keyring."""
    with _LOCK:
        with _ring_file_lock():
            return _sync_ring()


def key_metadata():
    ring = get_keyring()
    return {
        "current_id": ring["current_id"],
        "keys": [
            {"id": key["id"], "algorithm": key["algorithm"],
             "created_at": key["created_at"], "active": key["id"] == ring["current_id"]}
            for key in ring["keys"]
        ],
    }


def key_rotation():
    """Activate a new AES-GCM key, preserving the entire historical keyring."""
    with _LOCK:
        with _ring_file_lock():
            ring = _sync_ring()
            raw = secrets.token_bytes(32)
            _insert(ring, raw, "AES_GCM", "rotation")
            ring["current_id"] = _key_id(raw)
            _save_ring(ring)
            return ring["current_id"]


def _key_bytes(ring, kid, algorithm):
    for item in ring["keys"]:
        if item["id"] == kid and item["algorithm"] == algorithm:
            key = base64.b64decode(item["material"], validate=True)
            if len(key) not in (16, 24, 32):
                raise ValueError("Invalid key material")
            return key
    raise ValueError("Required historical encryption key is unavailable")


def is_versioned(value):
    return isinstance(value, str) and (value.startswith(_VERSION + ":") or value.startswith("v2f:"))


def encrypted_key_id(value):
    if isinstance(value, str) and value.startswith("v2f:"):
        value = _read_external(value)
    if isinstance(value, str) and value.startswith(_VERSION + ":"):
        sections = value.split(":", 2)
        if len(sections) != 3:
            raise ValueError("Malformed ciphertext envelope")
        return sections[1]
    return None


def encrypt_string(value, max_length=None, ring=None):
    if not isinstance(value, str):
        raise TypeError("Plaintext must be a string")
    ring = ring or get_keyring()
    kid = ring.get("current_id")
    if not kid:
        raise ValueError("No active GCM key; provision it explicitly before writing")
    raw = _key_bytes(ring, kid, "AES_GCM")
    cipher = AES.new(raw, AES.MODE_GCM, nonce=secrets.token_bytes(_NONCE_SIZE), mac_len=_TAG_SIZE)
    cipher.update(("reporting-dashboard:" + _VERSION + ":" + kid).encode("ascii"))
    ciphertext, tag = cipher.encrypt_and_digest(value.encode("utf-8"))
    packed = cipher.nonce + tag + ciphertext
    result = _VERSION + ":" + kid + ":" + base64.b64encode(packed).decode("ascii")
    if max_length is None or max_length == -1 or len(result) <= max_length:
        return result
    if max_length < 36:
        raise ValueError("Existing SQL column cannot hold a file reference")
    file_id = uuid.uuid4().hex
    inner = encrypt_string("ref:" + file_id + ":" + value, ring=ring)
    _atomic_write(_root() / "values" / (file_id + ".enc"), inner)
    return "v2f:" + file_id


def _read_external(reference):
    file_id = reference[4:]
    if not reference.startswith("v2f:") or len(file_id) != 32 or any(ch not in "0123456789abcdef" for ch in file_id):
        raise ValueError("Malformed external ciphertext reference")
    content = (_root() / "values" / (file_id + ".enc")).read_text(encoding="utf-8")
    if len(content) > 1000000 or not content.startswith("v2:"):
        raise ValueError("Invalid external ciphertext")
    return content


def _decrypt_v2(value, ring):
    chunks = value.split(":", 2)
    if len(chunks) != 3:
        raise ValueError("Malformed encrypted envelope")
    _, kid, encoded = chunks
    packed = base64.b64decode(encoded, validate=True)
    if len(packed) < _NONCE_SIZE + _TAG_SIZE:
        raise ValueError("Truncated encrypted envelope")
    raw = _key_bytes(ring, kid, "AES_GCM")
    nonce, tag, encrypted = packed[:_NONCE_SIZE], packed[_NONCE_SIZE:28], packed[28:]
    cipher = AES.new(raw, AES.MODE_GCM, nonce=nonce, mac_len=_TAG_SIZE)
    cipher.update(("reporting-dashboard:" + _VERSION + ":" + kid).encode("ascii"))
    return cipher.decrypt_and_verify(encrypted, tag).decode("utf-8")


def _legacy_ciphertext(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        decoded = base64.b64decode(value, validate=True)
        return bool(decoded) and len(decoded) % AES.block_size == 0
    except (ValueError, binascii.Error):
        return False


def _decrypt_legacy(value, ring):
    if os.getenv("CRYPTO_LEGACY_MODE", "").upper() != "AES_ECB_PKCS7":
        raise ValueError("Unversioned ciphertext requires verified CRYPTO_LEGACY_MODE=AES_ECB_PKCS7")
    if not _legacy_ciphertext(value):
        raise ValueError("Unrecognized legacy ciphertext")
    raw_value = base64.b64decode(value, validate=True)
    for item in ring["keys"]:
        if item["algorithm"] != "AES_ECB_PKCS7":
            continue
        try:
            decrypted = AES.new(_key_bytes(ring, item["id"], "AES_ECB_PKCS7"), AES.MODE_ECB).decrypt(raw_value)
            size = decrypted[-1]
            if not 1 <= size <= 16 or decrypted[-size:] != bytes([size]) * size:
                continue
            return decrypted[:-size].decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
    raise ValueError("Cannot authenticate or decrypt legacy ciphertext with available keys")


def decrypt_string(value, ring=None):
    if not isinstance(value, str):
        raise TypeError("Ciphertext must be a string")
    ring = ring or get_keyring()
    if value.startswith("v2f:"):
        plaintext = _decrypt_v2(_read_external(value), ring)
        prefix = "ref:" + value[4:] + ":"
        if not plaintext.startswith(prefix):
            raise ValueError("File reference authentication failed")
        return plaintext[len(prefix):]
    if is_versioned(value):
        return _decrypt_v2(value, ring)
    return _decrypt_legacy(value, ring)


def is_encrypted(value):
    # Conservative classification: unknown legacy blocks MUST NOT be encrypted again.
    return is_versioned(value) or _legacy_ciphertext(value)


def encrypt_decrypt_string(input_string, mode="encrypt"):
    if mode == "encrypt":
        return encrypt_string(input_string)
    if mode == "decrypt":
        return decrypt_string(input_string)
    raise ValueError("Mode must be 'encrypt' or 'decrypt'")


def verify_legacy_probe():
    """Require a known pre-production ECB vector before any bulk rewrite.

    Operators may set both CRYPTO_LEGACY_SAMPLE_CIPHERTEXT (base64) and
    CRYPTO_LEGACY_SAMPLE_SHA256 (hex digest of *known* plaintext). Without
    these, bulk migration of unversioned data is deliberately blocked.
    """
    from config import get_env_value
    sample = os.getenv("CRYPTO_LEGACY_SAMPLE_CIPHERTEXT") or get_env_value("CRYPTO_LEGACY_SAMPLE_CIPHERTEXT")
    digest = os.getenv("CRYPTO_LEGACY_SAMPLE_SHA256") or get_env_value("CRYPTO_LEGACY_SAMPLE_SHA256")
    if not sample or not digest or len(digest) != 64:
        raise ValueError("Verified legacy sample ciphertext and SHA-256 are required for migration")
    plaintext = _decrypt_legacy(sample, get_keyring())
    if not secrets.compare_digest(hashlib.sha256(plaintext.encode("utf-8")).hexdigest(), digest.lower()):
        raise ValueError("Legacy algorithm/key validation vector did not match")
    return True
