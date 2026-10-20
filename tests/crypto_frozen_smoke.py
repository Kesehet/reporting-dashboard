"""Exercise real PyInstaller crypto import and legacy .env reads.

This must work in a onefile executable, including when neither dotenv nor an
ENCRYPTION_KEY process variable was initialized before helper import.
No production keys, database, or server environment are accessed.
"""
import base64
import os
import sys
import tempfile
from pathlib import Path

from Crypto.Cipher import AES


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        os.chdir(root)
        os.environ["CRYPTO_STATE_DIR"] = str(root / "crypto-state")
        os.environ.pop("ENCRYPTION_KEY", None)
        os.environ.pop("CRYPTO_LEGACY_MODE", None)
        os.environ.pop("CRYPTO_LEGACY_ENV_FILE", None)
        raw_key = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        (root / ".env").write_text(
            "ENCRYPTION_KEY=" + raw_key.decode("ascii") + "\n", encoding="utf-8"
        )
        if not getattr(sys, "frozen", False):
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))

        # This import used to crash because it performed a GCM demo at import time.
        from helper import encryption_helper as crypto

        plaintext = "Real legacy ECB data"
        data = plaintext.encode("utf-8")
        pad = AES.block_size - len(data) % AES.block_size
        ciphertext = base64.b64encode(
            AES.new(raw_key, AES.MODE_ECB).encrypt(data + bytes([pad] * pad))
        ).decode("ascii")
        assert crypto.decrypt_string(ciphertext) == plaintext
        assert crypto._key_id(raw_key) in {
            entry["id"] for entry in crypto.get_keyring()["keys"]
        }
        assert not (root / "enc.key").exists(), "Import created an unwanted key"
        assert not (root / "old_enc.key").exists(), "Import rewrote a legacy key"
        print("PASS: frozen startup, env key discovery and legacy ECB decryption")


if __name__ == "__main__":
    main()
