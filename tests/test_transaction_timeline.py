"""Synthetic workflow fixtures; no Journey Manager credentials or network needed."""
from report_modules.transaction_timeline import build_timeline


def test_timeline_preserves_steps_and_links_comments():
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


def test_repeated_step_does_not_guess_task_or_comment():
    job = {"steps": [
        {"name": "Review", "jobActions": [{"submission": "same"}]},
        {"name": "Review", "jobActions": [{"submission": "same"}]},
    ], "txns": [{"submitKey": "same", "trackingCode": "C-TASK"}],
        "comments": [{"jobStep": "Review", "message": "Ambiguous"}]}
    result = build_timeline(job)
    assert all(not step["tasks"] and not step["comments"] for step in result["steps"])
    assert result["unassigned_tasks"][0]["tracking_code"] == "C-TASK"
    assert result["unassigned_comments"][0]["message"] == "Ambiguous"
