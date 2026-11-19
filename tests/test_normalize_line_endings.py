"""Regression tests for safe cross-platform build artifact normalization."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.normalize_line_endings import normalize_file


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "normalize_line_endings.py"


class LineEndingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.file = Path(self.directory.name) / "asset-manifest.json"

    def test_mixed_endings_become_lf(self):
        self.file.write_bytes(b'{"one":1,\r\n"two":2,\r"three":3\n}')
        self.assertTrue(normalize_file(self.file, "lf"))
        self.assertEqual(self.file.read_bytes(), b'{"one":1,\n"two":2,\n"three":3\n}')

    def test_lf_becomes_crlf(self):
        self.file.write_bytes(b"line1\nline2\r\nline3\r")
        self.assertTrue(normalize_file(self.file, "crlf"))
        self.assertEqual(self.file.read_bytes(), b"line1\r\nline2\r\nline3\r\n")

    def test_idempotent(self):
        self.file.write_bytes(b"already\nLF\n")
        self.assertFalse(normalize_file(self.file, "lf"))
        self.assertEqual(self.file.read_bytes(), b"already\nLF\n")

    def test_preserves_unicode_and_bom(self):
        self.file.write_bytes(b"\xef\xbb\xbf" + "café".encode("utf-8") + b"\r\n")
        self.assertTrue(normalize_file(self.file, "lf"))
        self.assertEqual(self.file.read_bytes(), b"\xef\xbb\xbf" + "café".encode("utf-8") + b"\n")

    def test_rejects_binary_without_modification(self):
        payload = b"binary\x00\r\nkeep"
        self.file.write_bytes(payload)
        with self.assertRaises(ValueError):
            normalize_file(self.file, "lf")
        self.assertEqual(self.file.read_bytes(), payload)

    def test_rejects_non_utf8_without_modification(self):
        payload = b"legacy-\xff\r\n"
        self.file.write_bytes(payload)
        with self.assertRaises(ValueError):
            normalize_file(self.file, "lf")
        self.assertEqual(self.file.read_bytes(), payload)

    def test_missing_build_manifest_is_safe(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--to", "lf", "--if-exists", str(self.file)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Skipping missing file", proc.stdout)

    def test_cli_normalizes_manifest(self):
        self.file.write_bytes(b'{"files":{}}\r\n')
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--to", "lf", str(self.file)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.file.read_bytes(), b'{"files":{}}\n')


if __name__ == "__main__":
    unittest.main()
