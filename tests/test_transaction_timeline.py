"""Synthetic transaction history fixtures; no Journey Manager credentials or network needed."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.transaction_timeline import build_timeline, load_timeline, merge_job_transactions


class TransactionTimelineTests(unittest.TestCase):
    def test_all_transactions_are_shown_with_their_comments_in_time_order(self):
        job = {
            "jobRefNumber": "C-ROOT", "status": "In Progress",
            "steps": [{"name": "Start"}, {"name": "Approve Application"}, {"name": "LOS Submitted"}],
            "txns": [
                {"trackingCode": "C-ROOT", "timeCreated": "2026-11-23T21:03:00-05:00"},
                {"trackingCode": "C-REVIEW", "groupName": "Loans Approved",
                 "timeCreated": "2026-11-27T15:24:00-05:00",
                 "comments": [{"message": "Review note", "timeAdded": "2026-11-27T16:17:00-05:00"}]},
                {"trackingCode": "C-LOS", "groupName": "LOS Submitted",
                 "formStatus": "Assigned", "timeCreated": "2026-11-27T16:17:00-05:00"},
                {"trackingCode": "C-ADDRESS", "timeCreated": "2026-11-27T15:24:00-05:00"},
            ],
        }
        result = build_timeline(job)
        self.assertNotIn("steps", result)
        self.assertNotIn("unassigned_tasks", result)
        self.assertEqual([t["tracking_code"] for t in result["transactions"]],
                         ["C-LOS", "C-REVIEW", "C-ADDRESS", "C-ROOT"])
        self.assertEqual(result["transactions"][1]["comments"][0]["message"], "Review note")
        self.assertEqual(result["transactions"][1]["comments"][0]["time"], "2026-11-27T16:17:00-05:00")

    def test_comments_are_attached_only_to_explicit_owner(self):
        job = {
            "steps": [{"jobActions": [{"jobActionKey": "a", "submission": "s2"}]}],
            "txns": [{"trackingCode": "C-ROOT", "submitKey": "s1"},
                     {"trackingCode": "C-TASK", "submitKey": "s2", "comments": [{"message": "Task note"}]}],
            "comments": [{"jobActionKey": "a", "message": "Action note"},
                         {"trackingCode": "C-ROOT", "message": "Root note"},
                         {"message": "Application note"}],
        }
        result = build_timeline(job)
        root, task = result["transactions"]
        self.assertEqual([n["message"] for n in root["comments"]], ["Root note"])
        self.assertEqual([n["message"] for n in task["comments"]], ["Task note", "Action note"])
        self.assertEqual([n["message"] for n in result["application_comments"]], ["Application note"])

    def test_duplicate_application_copy_does_not_repeat_task_note(self):
        note = {"message": "Same note", "timeAdded": "2026-11-23T09:00:00-05:00"}
        result = build_timeline({"txns": [{"trackingCode": "C-TASK", "comments": [note, note]}],
                                 "comments": [note]})
        self.assertEqual(len(result["transactions"][0]["comments"]), 1)
        self.assertEqual(result["application_comments"], [])

    def test_task_code_resolves_parent_job_and_requests_comments(self):
        workspace = Mock(base_url="https://workspace.example")
        responses = [
            {"result": [{"trackingCode": "C-TASK", "job": {"jobRefNumber": "C-ROOT"}}], "totalCount": 1},
            {"result": [{"jobRefNumber": "C-ROOT", "txns": [{"trackingCode": "C-ROOT"}]}], "totalCount": 1},
        ]
        workspace.session.post.side_effect = [
            SimpleNamespace(status_code=200, json=lambda payload=payload: payload)
            for payload in responses
        ]
        result = load_timeline(workspace, "C-TASK")
        self.assertEqual(result["job_reference"], "C-ROOT")
        self.assertEqual({t["tracking_code"] for t in result["transactions"]}, {"C-TASK", "C-ROOT"})
        query = workspace.session.post.call_args_list[-1].kwargs["json"]
        self.assertIn("txns.comments", query["attributes"])
        self.assertIn("'C-ROOT'", query["filters"][0]["criteria"][0])

    def test_merge_preserves_keys_and_notes_and_excludes_other_jobs(self):
        job = {"jobRefNumber": "C-ROOT",
               "txns": [{"trackingCode": "C-TASK", "comments": [{"message": "Note"}]}]}
        job["txns"] = merge_job_transactions(job, [
            {"trackingCode": "C-TASK", "submitKey": "review-key", "job": {"jobRefNumber": "C-ROOT"}},
            {"trackingCode": "C-OTHER", "job": {"jobRefNumber": "C-OTHER"}},
        ])
        result = build_timeline(job)
        self.assertEqual(len(result["transactions"]), 1)
        self.assertEqual(result["transactions"][0]["tracking_code"], "C-TASK")
        self.assertEqual(result["transactions"][0]["comments"][0]["message"], "Note")

    def test_missing_submission_is_retained_without_step_mapping(self):
        workspace = Mock(base_url="https://workspace.example")
        responses = [
            {"result": [{"trackingCode": "C-ROOT", "job": {"jobRefNumber": "C-ROOT"}}], "totalCount": 1},
            {"result": [{"jobRefNumber": "C-ROOT", "steps": [
                {"name": "Review", "jobActions": [{"submission": "review-key"}]},
            ]}], "totalCount": 1},
            {"result": [{"trackingCode": "C-TASK", "submitKey": "review-key",
                         "comments": [{"message": "Note"}]}], "totalCount": 1},
        ]
        workspace.session.post.side_effect = [
            SimpleNamespace(status_code=200, json=lambda payload=payload: payload)
            for payload in responses
        ]
        result = load_timeline(workspace, "C-ROOT")
        self.assertEqual({t["tracking_code"] for t in result["transactions"]}, {"C-ROOT", "C-TASK"})
        query = workspace.session.post.call_args_list[-1].kwargs["json"]
        self.assertEqual(query["filters"][0]["criteria"], ["submitKey IN ('review-key')"])

    def test_optional_submission_failure_keeps_available_transactions(self):
        workspace = Mock(base_url="https://workspace.example")
        workspace.session.post.side_effect = [
            SimpleNamespace(status_code=200, json=lambda: {
                "result": [{"trackingCode": "C-ROOT", "job": {"jobRefNumber": "C-ROOT"}}], "totalCount": 1}),
            SimpleNamespace(status_code=200, json=lambda: {
                "result": [{"jobRefNumber": "C-ROOT", "txns": [{"trackingCode": "C-ROOT"},
                    {"trackingCode": "C-TASK", "comments": [{"message": "Existing note"}]}],
                    "steps": [{"jobActions": [{"submission": "missing-key"}]}]}], "totalCount": 1}),
            SimpleNamespace(status_code=400),
        ]
        result = load_timeline(workspace, "C-ROOT")
        self.assertEqual({t["tracking_code"] for t in result["transactions"]}, {"C-ROOT", "C-TASK"})
        task = next(t for t in result["transactions"] if t["tracking_code"] == "C-TASK")
        self.assertEqual(task["comments"][0]["message"], "Existing note")
