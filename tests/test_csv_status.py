import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api-server'))

from csvLoader import list_csv_report_files, get_tracking_code_missing_reason, deduplicate_tracking_codes


class CsvReportStatusTests(unittest.TestCase):
    def test_list_csv_report_files_marks_loaded_and_pending_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, 'already_loaded.csv')
            file_b = os.path.join(tmpdir, 'new_report.csv')

            with open(file_a, 'w', encoding='utf-8', newline='') as f:
                f.write('eCA Tracking Code,Primary Name\nB-100,Alpha\nC-200,Beta\n')
            with open(file_b, 'w', encoding='utf-8', newline='') as f:
                f.write('eCA Tracking Code,Primary Name\nB-300,Gamma\n')

            status = list_csv_report_files(tmpdir, processed_files={'already_loaded.csv'})

            self.assertEqual(len(status), 2)
            file_map = {item['name']: item for item in status}
            self.assertEqual(file_map['already_loaded.csv']['status'], 'loaded')
            self.assertEqual(file_map['already_loaded.csv']['row_count'], 2)
            self.assertEqual(file_map['new_report.csv']['status'], 'pending')
            self.assertEqual(file_map['new_report.csv']['row_count'], 1)

    def test_get_tracking_code_missing_reason_returns_specific_reason(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'reasons.csv')
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write('eCA Tracking Code,Primary Name,App Start Date\nTEST-123,Test User,2026-08-28 14:19:06\n')

            reason = get_tracking_code_missing_reason('reasons.csv', 'TEST-123', tmpdir)
            self.assertIn('test', reason.lower())
            self.assertIn('test user', reason.lower())

    def test_deduplicate_tracking_codes_handles_pandas_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'duplicates.csv')
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write('eCA Tracking Code,Primary Name,AppStartDate\nB-100,Alpha,2026-01-01\nB-100,Alpha,2026-01-01\n')

            from csvLoader import read_file
            rows = [row for _, row in read_file(file_path).iterrows()]
            deduplicated = deduplicate_tracking_codes(rows)
            self.assertEqual(len(deduplicated), 1)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
