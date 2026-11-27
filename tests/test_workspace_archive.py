from pathlib import Path
import json
import sys
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.workspace_archive import (save_snapshot, read_archive, scan_txns, supplement_exact_search,
    merge_workspace_dump, decode_dump, ensure_archive, migrate_previous_archive)


class WorkspaceArchiveTests(unittest.TestCase):
    def test_snapshot_is_plain_json_in_existing_table(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = None
        self.assertTrue(save_snapshot(connection, "C-ROOT", {
            "jobRefNumber": "C-ROOT", "txns": [{"trackingCode": "C-TASK",
              "comments": [{"message": "synthetic note"}]}]}))
        calls = cursor.execute.call_args_list
        raw, snapshots = decode_dump(calls[1].args[1][5])
        self.assertEqual(raw[0]["trackingCode"], "C-TASK")
        self.assertEqual(snapshots[0]["job"]["txns"][0]["comments"][0]["message"], "synthetic note")
        self.assertIn("[DigitalReport].[dbo].[WorkspaceExtract]", calls[1].args[0])
        self.assertNotIn("CREATE TABLE", str(calls))
        connection.commit.assert_called_once()

    def test_identical_snapshot_does_not_append_again(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = None
        job = {"jobRefNumber": "C-ROOT", "txns": [{"trackingCode": "C-ROOT"}]}
        self.assertTrue(save_snapshot(connection, "C-ROOT", job))
        dump = cursor.execute.call_args_list[1].args[1][5]
        cursor.fetchone.return_value = (dump, "C-ROOT")
        self.assertFalse(save_snapshot(connection, "C-ROOT", job))
        self.assertIn("SELECT dump", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_count, 3)
        _, snapshots = decode_dump(dump)
        self.assertEqual(len(snapshots), 1)

    def test_legacy_writer_preserves_archive_xml_and_notes(self):
        old = json.dumps([{"trackingCode": "C-TASK", "submissionXml": "<Root/>",
                           "properties": {"old": "value"}, "comments": [{"message": "Old"}],
                           "_reportingTimelineArchive": [{"hash": "a", "job": {}}]}])
        result = merge_workspace_dump(old, [{"trackingCode": "C-TASK",
             "properties": {"new": "value"}, "comments": [{"message": "New"}]}])
        raw, snapshots = decode_dump(result)
        self.assertEqual(raw[0]["submissionXml"], "<Root/>")
        self.assertEqual(raw[0]["properties"], {"old": "value", "new": "value"})
        self.assertEqual(len(raw[0]["comments"]), 2)
        self.assertEqual(snapshots[0]["hash"], "a")
        self.assertIsInstance(json.loads(result), list)

    def test_archive_retains_older_tasks_and_comments(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = ("C-ROOT",)
        cursor.fetchall.return_value = [("C-TASK", json.dumps([{"trackingCode": "C-TASK",
          "_reportingTimelineArchive": [
            {"hash": "a", "capturedAt": "2026-11-22T00:00:00Z", "job": {"jobRefNumber": "C-ROOT",
                "txns": [{"trackingCode": "C-TASK", "comments": [{"message": "Old note"}]}]}},
            {"hash": "b", "capturedAt": "2026-11-23T00:00:00Z", "job": {"jobRefNumber": "C-ROOT",
                "txns": [{"trackingCode": "C-NEW"}]}}
          ]}]))]
        result = read_archive(connection, "C-TASK")
        self.assertEqual(result["source"], "archive")
        self.assertEqual({t["tracking_code"] for t in result["transactions"]}, {"C-TASK", "C-NEW"})
        task = next(t for t in result["transactions"] if t["tracking_code"] == "C-TASK")
        self.assertEqual(task["comments"][0]["message"], "Old note")

    def test_existing_table_validation_does_not_create_tables(self):
        connection = Mock()
        ensure_archive(connection)
        self.assertIn("SELECT TOP 0", connection.cursor.return_value.execute.call_args.args[0])

    def test_previous_archive_absent_is_safe(self):
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = (None,)
        migrate_previous_archive(connection)
        self.assertEqual(connection.cursor.return_value.execute.call_count, 1)

    def test_scan_paginates_without_status_or_form_filter(self):
        workspace = Mock(base_url="https://example")
        workspace.session.post.side_effect = [
            Mock(status_code=200, json=lambda: {"result": [{"trackingCode": "A"}], "totalCount": 2}),
            Mock(status_code=200, json=lambda: {"result": [{"trackingCode": "B"}], "totalCount": 2}),
        ]
        self.assertEqual([t["trackingCode"] for t in scan_txns(workspace, "2026-11-22", "2026-11-23")], ["A", "B"])
        requests = [call.kwargs["json"] for call in workspace.session.post.call_args_list]
        self.assertEqual(requests[1]["fetchOffset"], 1)
        self.assertNotIn("formStatus IN", str(requests))

    @patch("report_modules.workspace_archive.archived_history")
    def test_exact_search_can_find_purged_transaction(self, history):
        history.return_value = {"transactions": [{"tracking_code": "C-OLD", "name": "Consumer Loan", "status": "Completed"}]}
        result = supplement_exact_search({"headers": ["-"], "rows": [["No txns found"]]}, ["C-OLD"])
        self.assertEqual(result["rows"][0][result["headers"].index("tracking_code")], "C-OLD")
        self.assertEqual(result["rows"][0][result["headers"].index("Source")], "Archived SQL")
