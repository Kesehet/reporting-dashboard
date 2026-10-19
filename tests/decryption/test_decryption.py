"""Tests for both merged decryption APIs and old/new authenticated GCM values."""
import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from Crypto.Cipher import AES
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "api-server"))
from helper import encryption_helper as crypto
from helper import crypto_rotation as rot
from decrypt_tools import decrypt_tools
ACCESS="long-operator-access-token-for-tests-2026"
ADMIN="long-crypto-administrator-token-for-tests"
KEY=bytes(range(32))

class DecryptionCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd=os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir,self.cwd)
        env=patch.dict(os.environ,{"CRYPTO_STATE_DIR":self.temp.name,"ENCRYPTION_KEY":"",
            "CRYPTO_LEGACY_MODE":"","DECRYPT_TOOL_API_KEY":ACCESS,
            "DECRYPT_TOOL_ALLOWED_ORIGINS":"http://localhost:3000","CRYPTO_ADMIN_TOKEN":ADMIN})
        env.start()
        self.addCleanup(env.stop)
        mock_legacy=patch.object(crypto,"_legacy_env",return_value=None)
        mock_legacy.start()
        self.addCleanup(mock_legacy.stop)
        Path("enc.key").write_text(base64.b64encode(KEY).decode())
        crypto.key_rotation()
        app=Flask(__name__)
        app.register_blueprint(decrypt_tools)
        app.register_blueprint(rot.crypto_api)
        self.client=app.test_client()

    def previous_gcm(self,value):
        cipher=AES.new(KEY,AES.MODE_GCM,nonce=b"N"*12)
        payload,tag=cipher.encrypt_and_digest(value.encode())
        return "v2:"+base64.b64encode(cipher.nonce+tag+payload).decode()

    def post(self,value,token=ACCESS,origin=None):
        headers={"X-Decrypt-Access-Key":token}
        if origin:headers["Origin"]=origin
        return self.client.post("/tools/decrypt",json={"ciphertext":value},headers=headers)

    def test_unicode_new_format_and_nonce_uniqueness(self):
        for text in ("","Hello","اردو مرحبا 🌙","X"*10000):
            a=crypto.encrypt_string(text)
            b=crypto.encrypt_string(text)
            self.assertNotEqual(a,b)
            self.assertEqual(crypto.decrypt_string(a),text)

    def test_retained_earlier_gcm_format_and_key_rotation(self):
        old=self.previous_gcm("previous dashboard")
        self.assertEqual(crypto.decrypt_string(old),"previous dashboard")
        crypto.key_rotation()
        self.assertEqual(crypto.decrypt_string(old),"previous dashboard")
        self.assertEqual(len(crypto.key_metadata()["keys"]),3)

    def test_both_admin_interfaces_decrypt_both_generations(self):
        for expected,encrypted in (("modern",crypto.encrypt_string("modern")),
                                   ("old",self.previous_gcm("old"))):
            response=self.post(encrypted)
            self.assertEqual(response.status_code,200,response.get_data(as_text=True))
            self.assertEqual(response.json["plaintext"],expected)
            self.assertIn("no-store",response.headers["Cache-Control"])
            response=self.client.post("/crypto/decrypt",
                json={"value":encrypted},headers={"X-Crypto-Admin-Token":ADMIN})
            self.assertEqual(response.status_code,200,response.get_data(as_text=True))
            self.assertEqual(response.json["plaintext"],expected)

    def test_authenticated_tampering_fails_for_both_formats(self):
        for value in (self.previous_gcm("secret"),crypto.encrypt_string("secret")):
            parts=value.split(":")
            encoded=parts[-1]
            payload=bytearray(base64.b64decode(encoded))
            payload[12]^=1
            forged=":".join(parts[:-1]+[base64.b64encode(payload).decode()])
            with self.assertRaises(ValueError):
                crypto.decrypt_string(forged)
            self.assertEqual(self.post(forged).status_code,422)

    def test_invalid_input_and_cannot_guess_missing_keys(self):
        for value in ("v2:!","v2:AA==","v2:made-up:!!","ordinary text"):
            with self.assertRaises(ValueError):
                crypto.decrypt_string(value)
        self.assertTrue(crypto.is_encrypted("v2:bad"))
        self.assertFalse(crypto.is_encrypted("plain"))
        keyring=crypto.get_keyring()
        keyring["keys"]=[]
        crypto._save_ring(keyring)
        with self.assertRaises(ValueError):
            crypto.decrypt_string(self.previous_gcm("unavailable"))

    def test_no_secret_generated_without_explicit_rotation(self):
        self.assertFalse(Path("old_enc.key").exists())
        self.assertEqual(crypto.get_keyring()["current_id"],crypto.key_metadata()["current_id"])

    def test_access_denied_invalid_json_and_cors(self):
        encoded=crypto.encrypt_string("never reveal")
        for token in ("","wrong",ACCESS[:-1]):
            response=self.post(encoded,token)
            self.assertEqual(response.status_code,403)
            self.assertNotIn("never reveal",response.get_data(as_text=True))
        self.assertEqual(self.post(encoded,origin="https://bad.example").status_code,403)
        self.assertEqual(self.post(encoded,origin="http://localhost:3000").status_code,200)
        self.assertEqual(self.client.get("/crypto/status").status_code,403)
        self.assertEqual(self.client.get("/tools/decrypt").status_code,405)
        self.assertEqual(self.client.post("/tools/decrypt",data="bad",
          content_type="text/plain",headers={"X-Decrypt-Access-Key":ACCESS}).status_code,400)
        self.assertEqual(self.post("X"*65537).status_code,413)

    def test_configured_off_hides_tool_without_echoing_ciphertext(self):
        sample=self.previous_gcm("private")
        with patch.dict(os.environ,{"DECRYPT_TOOL_API_KEY":""}):
            response=self.post(sample)
            self.assertEqual(response.status_code,503)
        self.assertNotIn(sample,response.get_data(as_text=True))
        status=self.client.get("/crypto/status",headers={"X-Crypto-Admin-Token":ADMIN})
        self.assertEqual(status.status_code,200)
        self.assertNotIn('"material"',status.get_data(as_text=True))

if __name__=="__main__":
    unittest.main()
