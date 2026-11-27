"""Regression tests for the reported runtime failures (synthetic data only)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from csvLoader import read_file, prepare_rows
from report_modules.analytics import parse_quarters
from DB import _safe_read_query, _is_deadlock


class RuntimeHardeningTests(unittest.TestCase):
    def test_quarter_inputs(self):
        value = [{"year": 2026, "quarter": "Q2"}, {"year": 2025, "quarter": "Q4"}]
        import json
        expected = list(reversed(value))
        for payload in (value, json.dumps(value), str(value)):
            self.assertEqual(parse_quarters(payload), expected)
        self.assertEqual(value[0]["quarter"], "Q2")
        for invalid in ("not a list", "{}", [{"year": 2026, "quarter": "Q5"}]):
            with self.assertRaises(ValueError):
                parse_quarters(invalid)

    def test_bad_csv_fails_whole_import(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "malformed.csv"
            for data in ("code,name\nC-1,Ada\nC-2,Bob,extra\n",
                         "code,name\nC-1,Ada\nC-2\n"):
                path.write_text(data, encoding="utf-8")
                self.assertTrue(read_file(path).empty)
                with self.assertRaisesRegex(ValueError, "line 3"):
                    prepare_rows(path)
            path.write_text('code,name\nC-1,"Ada, Example"\n', encoding="utf-8")
            self.assertEqual(len(read_file(path)), 1)

    def test_read_retry_guard(self):
        self.assertTrue(_safe_read_query("SELECT COUNT(*) FROM T"))
        self.assertTrue(_safe_read_query(";WITH x AS (SELECT id FROM T) SELECT * FROM x"))
        self.assertFalse(_safe_read_query("SELECT * INTO T2 FROM T"))
        self.assertFalse(_safe_read_query("SELECT * FROM T; DELETE FROM T"))
        self.assertTrue(_is_deadlock(Exception("40001", "deadlock (1205)")))
        self.assertFalse(_is_deadlock(Exception("40001", "other error")))


if __name__ == "__main__":
    unittest.main()
