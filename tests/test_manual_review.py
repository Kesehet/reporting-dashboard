from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from report_modules.manual_review import build_report


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
