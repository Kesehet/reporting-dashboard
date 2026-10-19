"""High-signal crypto and API tests. No production secrets/database required."""
import base64
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))

from flask import Flask
from helper import encryption_helper as crypto
from decrypt_tools import decrypt_tools

ACCESS = "secure-operator-token-for-decrypt-tool-2026"
KEY_A = bytes(range(32))
KEY_B = bytes(reversed(range(32)))


class CryptoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.current = os.path.join(self.temp.name, "enc.key")
        self.previous = os.path.join(self.temp.name, "old_enc.key")
        p1 = patch.object(crypto, "CURRENT_KEY_FILE", self.current)
        p2 = patch.object(crypto, "OLD_KEY_FILE", self.previous)
        p1.start()
        p2.start()
        self.addCleanup(p2.stop)
        self.addCleanup(p1.stop)
        crypto.save_key(KEY_A, self.current)

    def test_round_trip_unicode_multiline_empty_and_long_values(self):
        for text in ("", "hello", "کیا حال ہے\nمرحبا 🌙", "X" * 10000):
            with self.subTest(text_length=len(text)):
                ciphertext = crypto.encrypt_decrypt_string(text)
                self.assertTrue(ciphertext.startswith("v2:"))
                self.assertNotEqual(ciphertext, text)
                self.assertEqual(crypto.encrypt_decrypt_string(ciphertext, "decrypt"), text)

    def test_random_nonce_changes_ciphertext_and_preserves_plaintext(self):
        a = crypto.encrypt_decrypt_string("same sensitive string")
        b = crypto.encrypt_decrypt_string("same sensitive string")
        self.assertNotEqual(a, b)
        self.assertEqual(crypto.encrypt_decrypt_string(a, "decrypt"), "same sensitive string")
        self.assertEqual(crypto.encrypt_decrypt_string(b, "decrypt"), "same sensitive string")

    def test_tampering_nonce_tag_and_ciphertext_is_detected(self):
        encrypted = crypto.encrypt_decrypt_string("protect me")
        payload = base64.b64decode(encrypted[3:])
        for position in (0, 12, len(payload) - 1):
            with self.subTest(position=position):
                damaged = bytearray(payload)
                damaged[position] ^= 1
                with self.assertRaises(ValueError):
                    crypto.encrypt_decrypt_string("v2:" + base64.b64encode(damaged).decode(), "decrypt")

    def test_wrong_key_fails_not_garbage_plaintext(self):
        ciphertext = crypto.encrypt_decrypt_string("confidential")
        crypto.save_key(KEY_B, self.current)
        with self.assertRaises(ValueError):
            crypto.encrypt_decrypt_string(ciphertext, "decrypt")

    def test_rotation_reads_previous_key(self):
        encrypted = crypto.encrypt_decrypt_string("old encrypted value")
        crypto.save_key(KEY_A, self.previous)
        crypto.save_key(KEY_B, self.current)
        self.assertEqual(crypto.encrypt_decrypt_string(encrypted, "decrypt"), "old encrypted value")
        fresh = crypto.encrypt_decrypt_string("new encrypted value")
        os.remove(self.previous)
        self.assertEqual(crypto.encrypt_decrypt_string(fresh, "decrypt"), "new encrypted value")
        with self.assertRaises(ValueError):
            crypto.encrypt_decrypt_string(encrypted, "decrypt")

    def test_legacy_values_are_not_double_encrypted_and_cannot_be_decrypted(self):
        legacy = base64.b64encode(b"ciphertextdata!!").decode()
        self.assertTrue(crypto.is_encrypted(legacy))
        with self.assertRaisesRegex(ValueError, "legacy"):
            crypto.encrypt_decrypt_string(legacy, "decrypt")
        self.assertFalse(crypto.is_encrypted("ordinary plain text"))

    def test_v2_recognition_including_corrupt_v2_protects_etl_data(self):
        encrypted = crypto.encrypt_decrypt_string("user")
        self.assertTrue(crypto.is_encrypted(encrypted))
        self.assertTrue(crypto.is_encrypted("v2:not base64"))
        self.assertFalse(crypto.is_encrypted(""))
        self.assertFalse(crypto.is_encrypted(None))

    def test_malformed_encoding_and_short_payload_are_rejected(self):
        for bad in ("v2:!", "v2:AA==", "v2:!!!!" + "a" * 100):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crypto.encrypt_decrypt_string(bad, "decrypt")

    def test_missing_key_never_generates_replacement(self):
        os.remove(self.current)
        with self.assertRaises(FileNotFoundError):
            crypto.encrypt_decrypt_string("plain", "encrypt")
        self.assertFalse(os.path.exists(self.current))

    def test_bad_key_file_is_rejected(self):
        with open(self.current, "w") as output:
            output.write("invalid!!")
        with self.assertRaises(ValueError):
            crypto.encrypt_decrypt_string("plain", "encrypt")
        with self.assertRaises(ValueError):
            crypto.save_key(b"short", self.current)


class DecryptEndpointTests(CryptoTests):
    def setUp(self):
        super().setUp()
        self.app = Flask(__name__)
        self.app.register_blueprint(decrypt_tools)
        self.client = self.app.test_client()
        self.env = patch.dict(os.environ, {
            "DECRYPT_TOOL_API_KEY": ACCESS,
            "DECRYPT_TOOL_ALLOWED_ORIGINS": "http://localhost:3000",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def post(self, body, access=ACCESS, origin=None, **kwargs):
        headers = {"X-Decrypt-Access-Key": access}
        if origin:
            headers["Origin"] = origin
        return self.client.post("/tools/decrypt", json=body, headers=headers, **kwargs)

    def test_authenticated_round_trip_and_no_cache(self):
        encrypted = crypto.encrypt_decrypt_string("bank account 🏦")
        response = self.post({"ciphertext": encrypted})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"plaintext": "bank account 🏦"})
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(response.headers["Pragma"], "no-cache")

    def test_missing_or_wrong_access_token_is_denied(self):
        encrypted = crypto.encrypt_decrypt_string("sensitive")
        for access in ("", "bad", ACCESS[:-1]):
            with self.subTest(access=access):
                response = self.post({"ciphertext": encrypted}, access=access)
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("sensitive", response.get_data(as_text=True))

    def test_tool_disabled_for_missing_or_short_access_configuration(self):
        for access in ("", "short"):
            with patch.dict(os.environ, {"DECRYPT_TOOL_API_KEY": access}):
                response = self.post({"ciphertext": "v2:abc"})
                self.assertEqual(response.status_code, 503)

    def test_cross_site_origins_are_blocked_but_explicit_allowed_origin_works(self):
        ciphertext = crypto.encrypt_decrypt_string("secret")
        response = self.post({"ciphertext": ciphertext}, origin="https://other.example")
        self.assertEqual(response.status_code, 403)
        response = self.post({"ciphertext": ciphertext}, origin="http://localhost:3000")
        self.assertEqual(response.status_code, 200)

    def test_empty_non_string_wrong_json_and_too_large_rejected(self):
        for body in (None, [], {}, {"ciphertext": 7}, {"ciphertext": ""}, {"ciphertext": "   "}):
            with self.subTest(body=body):
                response = self.post(body)
                self.assertEqual(response.status_code, 400)
        large = self.post({"ciphertext": "a" * 65537})
        self.assertEqual(large.status_code, 413)
        raw = self.client.post("/tools/decrypt", data="not json", headers={
            "Content-Type": "text/plain", "X-Decrypt-Access-Key": ACCESS,
        })
        self.assertEqual(raw.status_code, 400)

    def test_bad_mac_legacy_format_and_corrupt_payload_return_generic_error(self):
        encrypted = crypto.encrypt_decrypt_string("secret data")
        for value in ("not encrypted", "v2:!!", encrypted[:-2] + "AA"):
            with self.subTest(value=value):
                response = self.post({"ciphertext": value})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn(value, response.get_data(as_text=True))
                self.assertNotIn("secret data", response.get_data(as_text=True))
                self.assertIn("no-store", response.headers["Cache-Control"])

    def test_get_not_allowed_and_result_never_in_url(self):
        response = self.client.get("/tools/decrypt")
        self.assertEqual(response.status_code, 405)

    def test_no_key_files_produces_service_error(self):
        # Only files necessary for cryptographic operation are read.
        os.remove(self.current)
        response = self.post({"ciphertext": "v2:" + base64.b64encode(b"0" * 29).decode()})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(ACCESS, response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
