"""CSV encoding regression tests with synthetic customer data only."""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from csvLoader import read_file, list_csv_report_files


class CsvEncodingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, data):
        target = self.root / name
        target.write_bytes(data)
        return str(target)

    def test_non_ascii_first_occurs_at_byte_14402(self):
        # An old first-10-KB chardet guess would incorrectly report 'ascii'.
        prefix = b"eCA Tracking Code,Primary Name\nC-123,"
        payload = prefix + (b"A" * (14402 - len(prefix)))
        payload += "\u2019".encode("utf-8") + b"\n"
        self.assertEqual(payload.index(b"\xe2"), 14402)
        path = self.write("late_unicode.csv", payload)
        frame = read_file(path)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.loc[0, "eCA Tracking Code"], "C-123")
        self.assertTrue(frame.loc[0, "Primary Name"].endswith("\u2019"))
        status = list_csv_report_files(self.temp.name)
        self.assertEqual(status[0]["row_count"], 1)

    def test_windows_1252_customer_name_and_smart_punctuation(self):
        text = "eCA Tracking Code,Primary Name\nC-205,Ren\u00e9e\u2019s Caf\u00e9\n"
        path = self.write("windows_export.csv", text.encode("cp1252"))
        frame = read_file(path)
        self.assertEqual(frame.loc[0, "Primary Name"], "Ren\u00e9e\u2019s Caf\u00e9")

    def test_utf8_bom_is_not_returned_in_column_header(self):
        text = "eCA Tracking Code,Primary Name\nC-333,\u0627\u0644\u0623\u0645\u0644\n"
        frame = read_file(self.write("bom.CSV", text.encode("utf-8-sig")))
        self.assertEqual(list(frame.columns), ["eCA Tracking Code", "Primary Name"])
        self.assertEqual(frame.loc[0, "Primary Name"], "\u0627\u0644\u0623\u0645\u0644")

    def test_utf16_bom_and_utf16_without_bom_remain_supported(self):
        text = "eCA Tracking Code,Primary Name\nC-1,Zo\u00eb\n"
        for codec in ("utf-16", "utf-16-le", "utf-16-be"):
            with self.subTest(codec=codec):
                frame = read_file(self.write(codec + ".csv", text.encode(codec)))
                self.assertEqual(frame.loc[0, "Primary Name"], "Zo\u00eb")

    def test_unknown_binary_byte_does_not_get_silently_replaced(self):
        # CP1252 has no mapping for 0x81. Do not disguise it as Latin-1 data.
        path = self.write("undecodable.csv", b"eCA Tracking Code,Primary Name\nC-1,Bad\x81Name\n")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            frame = read_file(path)
            status = list_csv_report_files(self.temp.name)
        self.assertTrue(frame.empty)
        self.assertIn("Unable to decode CSV", captured.getvalue())
        self.assertEqual(status[0]["row_count"], 0)
        self.assertEqual(status[0]["status"], "pending")

    def test_corrupt_utf8_bom_does_not_fallback_to_cp1252(self):
        path = self.write("corrupt-bom.csv",
                          b"\xef\xbb\xbfeCA Tracking Code,Primary Name\nC-1,Broken\x92\n")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            self.assertTrue(read_file(path).empty)
        self.assertIn("Unable to decode CSV", captured.getvalue())

    def test_broken_csv_shape_does_not_get_reinterpreted_as_excel(self):
        path = self.write("broken.csv",
                          b'eCA Tracking Code,Primary Name\nC-1,"unterminated field\n')
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            self.assertTrue(read_file(path).empty)
        self.assertIn("Error reading file", captured.getvalue())

    def test_regular_csv_and_excel_work_as_before(self):
        text = "eCA Tracking Code,Primary Name\nC-99,Ada\n"
        frame = read_file(self.write("plain.csv", text.encode("ascii")))
        self.assertEqual(frame.loc[0, "Primary Name"], "Ada")
        excel_path = self.root / "plain.xlsx"
        frame.to_excel(excel_path, index=False)
        self.assertEqual(read_file(str(excel_path)).loc[0, "Primary Name"], "Ada")


if __name__ == "__main__":
    unittest.main()
