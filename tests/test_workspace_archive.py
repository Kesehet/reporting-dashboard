from pathlib import Path
import json
import sys
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.workspace_archive import save_snapshot, read_archive, scan_txns, supplement_exact_search


class WorkspaceArchiveTests(unittest.TestCase):
    def test_snapshot_is_plain_json_and_indexed(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = None
        self.assertTrue(save_snapshot(connection, "C-ROOT", {
            "jobRefNumber": "C-ROOT", "txns": [{"trackingCode": "C-TASK",
              "comments": [{"message": "sensitive synthetic note"}]}]}))
        calls = cursor.execute.call_args_list
        payload = json.loads(calls[1].args[1][2])
        self.assertEqual(payload["txns"][0]["comments"][0]["message"], "sensitive synthetic note")
        self.assertEqual(len(calls), 4)
        connection.commit.assert_called_once()

    def test_identical_snapshot_does_not_insert_again(self):
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = (1,)
        self.assertFalse(save_snapshot(connection, "C-ROOT", {"txns": []}))
        self.assertEqual(connection.cursor.return_value.execute.call_count, 2)

    def test_archive_retains_older_tasks_and_comments(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = (1,)
        cursor.fetchall.side_effect = [[("C-ROOT",)], [
            (datetime(2026, 11, 22), '{"jobRefNumber":"C-ROOT","txns":[{"trackingCode":"C-TASK","comments":[{"message":"Old note"}]}]}'),
            (datetime(2026, 11, 23), '{"jobRefNumber":"C-ROOT","txns":[{"trackingCode":"C-NEW"}]}'),
        ]]
        result = read_archive(connection, "C-ROOT")
        self.assertEqual(result["source"], "archive")
        self.assertEqual({t["tracking_code"] for t in result["transactions"]}, {"C-TASK", "C-NEW"})
        task = next(t for t in result["transactions"] if t["tracking_code"] == "C-TASK")
        self.assertEqual(task["comments"][0]["message"], "Old note")

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
