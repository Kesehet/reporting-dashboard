from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.manual_review import build_report, job_rows


class ManualReviewReportTests(unittest.TestCase):
    def test_review_outcome_and_completion_are_independent(self):
        task = {
            "submitKey": "review",
            "timeCompleted": "2026-11-21T12:00:00-05:00",
            "userLoginName": "reviewer",
            "comments": [{"message": "Reviewed"}, {"message": "Reviewed"}],
        }
        job = {
            "jobRefNumber": "C-A1",
            "status": "In Progress",
            "steps": [{
                "name": "Review Application",
                "status": "Completed",
                "result": "Approve",
                "jobActions": [{
                    "type": "Job Task Assign",
                    "submission": "review",
                    "timeActionExecuted": "2026-11-21T16:00:00Z",
                }],
            }],
            "txns": [task, {"comments": [{"message": "Unrelated note"}]}],
        }
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        row, = build_report([job, job], now)
        self.assertEqual(row["duration_seconds"], 3600)
        self.assertEqual(row["outcome"], "Approved")
        self.assertEqual(row["reviewer"], "reviewer")
        self.assertEqual(row["notes"], ["Reviewed"])
        self.assertFalse(row["completed"])
        completed, = build_report([{
            **job, "status": "Completed", "timeFinished": "2026-11-21T18:00:00Z",
        }], now)
        self.assertTrue(completed["completed"])

    def test_open_review_and_unreached_steps(self):
        job = {
            "jobRefNumber": "B-B1",
            "steps": [{
                "name": "Review Application",
                "status": "Pending",
            }],
        }
        now = datetime(2026, 11, 22, 18, tzinfo=timezone.utc)
        self.assertEqual(build_report([job], now), [])
        job["steps"][0].update(status="In Progress", timeCreated="2026-11-22T17:00:00Z")
        row, = build_report([job], now)
        self.assertEqual(row["application_type"], "Business")
        self.assertTrue(row["in_review"])
        self.assertFalse(row["completed"])
        self.assertEqual(row["duration_seconds"], 3600)
        self.assertIsNone(row["outcome"])

    def test_job_scan_loads_details_only_for_review_references(self):
        review = {"jobRefNumber": "C-A1", "steps": [{"name": "Review Application"}]}
        other = {"jobRefNumber": "C-A2", "steps": [{"name": "Application Start"}]}
        detail = {**review, "txns": [{"trackingCode": "C-A1"}]}
        workspace = Mock(base_url="https://workspace.example")
        workspace.session.post.side_effect = [
            SimpleNamespace(status_code=200, json=lambda: {"result": [other], "totalCount": 2}),
            SimpleNamespace(status_code=200, json=lambda: {"result": [review], "totalCount": 2}),
            SimpleNamespace(status_code=200, json=lambda: {"result": [detail], "totalCount": 1}),
        ]
        self.assertEqual(list(job_rows(workspace, "2026-11-21", "2026-11-23")), [detail])
        first, second, third = [
            call.kwargs["json"] for call in workspace.session.post.call_args_list
        ]
        self.assertEqual(first["attributes"], ["jobRefNumber", "steps"])
        self.assertEqual(second["fetchOffset"], 1)
        self.assertIn("txns.comments", third["attributes"])
        self.assertEqual(third["filters"][1]["criteria"], ["jobRefNumber IN ('C-A1')"])

    def test_workspace_channel_and_review_task_without_assignment_action(self):
        job = {
            "jobRefNumber": "C-B1",
            "status": "In Progress",
            "steps": [
                {"name": "Review Application", "status": "Completed",
                 "timeCreated": "2026-11-21T16:00:00Z",
                 "timeFinished": "2026-11-21T17:00:00Z"},
                {"name": "Approve Application", "status": "Completed"},
            ],
            "txns": [
                {"trackingCode": "C-B1", "properties": {"isBankerAssisted": True},
                 "comments": [{"message": "Unrelated"}]},
                {"trackingCode": "C-T1", "groupName": "Manual Review",
                 "formStatus": "Completed", "userLoginName": "reviewer",
                 "comments": [{"message": "Task note"}]},
            ],
            "comments": [
                {"trackingCode": "C-T1", "message": "Linked note"},
                {"trackingCode": "C-B1", "message": "Unrelated job note"},
            ],
        }
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        row, = build_report([job], now)
        self.assertEqual(row["channel"], "In-Branch")
        self.assertEqual(row["outcome"], "Approved")
        self.assertEqual(row["reviewer"], "reviewer")
        self.assertEqual(row["notes"], ["Task note", "Linked note"])
        self.assertFalse(row["completed"])
        job["txns"][0]["properties"]["isBankerAssisted"] = False
        online, = build_report([job], now)
        self.assertEqual(online["channel"], "Online")
