"""Synthetic workflow fixtures; no Journey Manager credentials or network needed."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.transaction_timeline import build_timeline, load_timeline



class TransactionTimelineTests(unittest.TestCase):
    def test_timeline_preserves_steps_and_links_comments(self):
        job = {
            "jobRefNumber": "C-ROOT", "status": "Completed",
            "steps": [
                {"name": "Start", "status": "Completed", "jobActions": [{"submission": "s1"}]},
                {"name": "Review Application", "status": "Completed", "jobActions": [
                    {"submission": "s2", "jobActionKey": "a2", "result": "Deny"}]},
                {"name": "Decline Application", "status": "Completed"},
                {"name": "Decline Application Complete", "status": "Completed"},
            ],
            "txns": [
                {"submitKey": "s2", "trackingCode": "C-REVIEW", "comments": [{"message": "Review note"}]},
                {"submitKey": "s1", "trackingCode": "C-ROOT"},
                {"submitKey": "unknown", "trackingCode": "C-OTHER"},
            ],
            "comments": [{"jobActionKey": "a2", "message": "Step note"}, {"message": "General note"}],
        }
        result = build_timeline(job)
        assert [s["sequence"] for s in result["steps"]] == [1, 2, 3, 4]
        review = result["steps"][1]
        assert review["result"] == "Deny"
        assert review["tasks"][0]["tracking_code"] == "C-REVIEW"
        assert review["tasks"][0]["comments"][0]["message"] == "Review note"
        assert review["comments"][0]["message"] == "Step note"
        assert result["steps"][2]["tasks"] == []
        assert result["unassigned_tasks"][0]["tracking_code"] == "C-OTHER"
        assert result["unassigned_comments"][0]["message"] == "General note"


    def test_repeated_step_does_not_guess_task_or_comment(self):
        job = {"steps": [
            {"name": "Review", "jobActions": [{"submission": "same"}]},
            {"name": "Review", "jobActions": [{"submission": "same"}]},
        ], "txns": [{"submitKey": "same", "trackingCode": "C-TASK"}],
            "comments": [{"jobStep": "Review", "message": "Ambiguous"}]}
        result = build_timeline(job)
        assert all(not step["tasks"] and not step["comments"] for step in result["steps"])
        assert result["unassigned_tasks"][0]["tracking_code"] == "C-TASK"
        assert result["unassigned_comments"][0]["message"] == "Ambiguous"

    def test_task_code_resolves_parent_job_and_requests_comments(self):
        workspace = Mock(base_url="https://workspace.example")
        responses = [
            {"result": [{"trackingCode": "C-TASK", "job": {"jobRefNumber": "C-ROOT"}}], "totalCount": 1},
            {"result": [{"jobRefNumber": "C-ROOT", "steps": [{"name": "Start"}]}], "totalCount": 1},
        ]
        workspace.session.post.side_effect = [
            SimpleNamespace(status_code=200, json=lambda payload=payload: payload)
            for payload in responses
        ]
        result = load_timeline(workspace, "C-TASK")
        self.assertEqual(result["job_reference"], "C-ROOT")
        query = workspace.session.post.call_args_list[-1].kwargs["json"]
        self.assertIn("txns.comments", query["attributes"])
        self.assertIn("'C-ROOT'", query["filters"][0]["criteria"][0])

    def test_comment_timestamp_uses_workspace_time_added(self):
        result = build_timeline({"steps": [{"name": "Review", "jobActions": [{"submission": "a"}]}],
            "txns": [{"submitKey": "a", "comments": [{"message": "Note", "timeAdded": "2026-11-23T09:00:00-05:00"}]}]})
        self.assertEqual(result["steps"][0]["tasks"][0]["comments"][0]["time"], "2026-11-23T09:00:00-05:00")

    def test_live_shape_without_submission_links(self):
        job = {
            "jobRefNumber": "C-ROOT",
            "steps": [
                {"name": "Start", "status": "Completed"},
                {"name": "Review Application", "status": "Completed"},
                {"name": "Decline Application", "status": "Completed"},
                {"name": "Decline Application Complete", "status": "Completed"},
            ],
            "txns": [
                {"trackingCode": "C-ROOT", "formName": "Consumer Loans"},
                {"trackingCode": "C-TASK", "groupName": "Manual Review", "comments": [{"message": "Synthetic note"}]},
            ],
        }
        result = build_timeline(job)
        start, review, decline, complete = result["steps"]
        self.assertEqual(start["tasks"][0]["tracking_code"], "C-ROOT")
        self.assertEqual(review["tasks"][0]["tracking_code"], "C-TASK")
        self.assertEqual(review["tasks"][0]["comments"][0]["message"], "Synthetic note")
        self.assertEqual(review["result"], "Deny (inferred)")
        self.assertEqual(start["result"], "Review Application (inferred)")
        self.assertFalse(decline["tasks"])
        self.assertFalse(complete["tasks"])
        self.assertFalse(result["unassigned_tasks"])

    def test_owner_action_wins_over_reused_submission(self):
        result = build_timeline({
            "steps": [
                {"name": "Review Application", "jobActions": [
                    {"type": "Job Task Assign", "submission": {"submitKey": "a"}},
                    {"type": "Job Task Wait", "routeResult": "Deny"},
                ]},
                {"name": "Decline Application", "jobActions": [
                    {"type": "Job Task Wait", "submission": "a"},
                ]},
            ],
            "txns": [{"submitKey": "a", "trackingCode": "C-TASK"}],
        })
        self.assertEqual(result["steps"][0]["tasks"][0]["tracking_code"], "C-TASK")
        self.assertEqual(result["steps"][0]["result"], "Deny")
        self.assertFalse(result["steps"][1]["tasks"])

    def test_multiple_review_tasks_or_steps_remain_unassigned(self):
        job = {"steps": [{"name": "Review Application", "status": "Completed"}],
               "txns": [{"groupName": "Manual Review", "trackingCode": "C-A"},
                        {"groupName": "Manual Review", "trackingCode": "C-B"}]}
        self.assertEqual(len(build_timeline(job)["unassigned_tasks"]), 2)
        job["steps"].append({"name": "Review Application", "status": "Completed"})
        job["txns"].pop()
        self.assertEqual(len(build_timeline(job)["unassigned_tasks"]), 1)
