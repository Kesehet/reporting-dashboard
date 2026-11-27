"""Read-only, on-demand application timeline from Journey Manager Workspaces."""
import re

from flask import Blueprint, current_app, jsonify, request
from requests import RequestException, Timeout

from authentication import unauthorized, verify_microsoft_token, verify_token
from role_filter import all_groups
from report_modules.manual_review import (
    REVIEW_STEPS, WorkspaceReportError, normalized, query_jobs, workflow_decision,
)

timeline_api = Blueprint("transaction_timeline", __name__)
CODE = re.compile(r"[A-Za-z0-9_-]{1,128}")
JOB_ATTRIBUTES = ["jobRefNumber", "status", "steps", "comments", "txns", "txns.comments"]
TXN_ATTRIBUTES = ["trackingCode", "submitKey", "job", "formName", "formStatus",
                  "groupName", "taskType", "userLoginName", "timeCreated",
                  "timeRequest", "timeCompleted", "timeUserLastModified", "comments"]


def records(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def text_value(value):
    return value if isinstance(value, str) else None


def comments(items):
    """Expose only display fields; preserve replies and do not return raw form data."""
    result = []
    for item in records(items):
        message = text_value(item.get("message"))
        if message:
            result.append({
                "message": message,
                "header": text_value(item.get("header")),
                "parent": text_value(item.get("parent")),
                "author": text_value(item.get("userLoginName") or item.get("loginName")
                                     or item.get("author") or item.get("userName")),
                "time": text_value(item.get("timeAdded") or item.get("timeCreated") or item.get("time")),
                "replies": comments(item.get("replies") or item.get("comments")),
            })
    return result


def unique_comments(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def task_view(txn):
    return {
        "tracking_code": text_value(txn.get("trackingCode")),
        "name": text_value(txn.get("formName")),
        "status": text_value(txn.get("formStatus")),
        "group": text_value(txn.get("groupName")),
        "user": text_value(txn.get("userLoginName")),
        "created": text_value(txn.get("timeCreated") or txn.get("timeRequest") or txn.get("timeRequested")),
        "updated": text_value(txn.get("timeUserLastModified") or txn.get("timeCompleted")),
        "comments": comments(txn.get("comments")),
    }


def identifiers(txn):
    return {value for key in ("submitKey", "trackingCode") if (value := txn.get(key))}


def action_matches(txn, actions):
    ids = identifiers(txn)
    for action in actions:
        submission = action.get("submission")
        if isinstance(submission, dict):
            submission_ids = identifiers(submission)
        else:
            submission_ids = {submission} if isinstance(submission, str) else set()
        if ids & submission_ids or (
            txn.get("jobActionKey") and txn["jobActionKey"] == action.get("jobActionKey")
        ):
            return True
    return False


def resolve_task_steps(job, steps, txns):
    """Prefer the task-owning action; later actions may reference the same submission."""
    actions = [records(step.get("jobActions") or step.get("actions")) for step in steps]
    matches = []
    for txn in txns:
        owners = [
            i for i, group in enumerate(actions) if action_matches(txn, [
                a for a in group if normalized(a.get("type")) in {"job form start", "job task assign"}
            ])
        ]
        direct = [i for i, group in enumerate(actions) if action_matches(txn, group)]
        matches.append(owners or direct)

    # Workspace versions may omit submission identifiers or repeat them in wait actions.
    # Only resolve a fallback when both the workflow step and the task are unique.
    starts = [i for i, s in enumerate(steps)
              if normalized(s.get("type")) == "start" or normalized(s.get("name")) in {"start", "application start"}]
    reviews = [i for i, s in enumerate(steps) if normalized(s.get("name")) in REVIEW_STEPS]
    reference = job.get("jobRefNumber")
    primary = [i for i, t in enumerate(txns) if reference and t.get("trackingCode") == reference]
    review = [i for i, t in enumerate(txns) if i not in primary and (
        normalized(t.get("groupName")) == "manual review" or normalized(t.get("taskType")) == "review"
    )]
    for candidates, targets in ((primary, starts), (review, reviews)):
        if len(candidates) != 1 or len(targets) != 1:
            continue
        task, step = candidates[0], targets[0]
        if len(matches[task]) != 1 and (not matches[task] or step in matches[task]):
            if not any(m == [step] for i, m in enumerate(matches) if i != task):
                matches[task] = [step]
    return matches


def build_timeline(job):
    """Keep source step order, including repeated names and zero-task steps.

    Prefer explicit submission/action identifiers, then unique application/review
    ownership evidence. Ambiguous tasks and comments remain separately visible.
    """
    steps = records(job.get("steps"))
    txns = records(job.get("txns"))
    job_comments = records(job.get("comments"))
    links = []
    for step in steps:
        actions = records(step.get("jobActions") or step.get("actions"))
        keys = {a["jobActionKey"] for a in actions if a.get("jobActionKey")}
        links.append(keys)

    matches = resolve_task_steps(job, steps, txns)
    mapped = [[txn for txn, indices in zip(txns, matches) if indices == [i]]
              for i in range(len(steps))]
    comment_matches = []
    for note in job_comments:
        note_ids = {note[k] for k in ("trackingCode", "submitKey") if note.get(k)}
        found = []
        for i, step in enumerate(steps):
            task_ids = set().union(*(identifiers(t) for t in mapped[i]))
            if (note.get("jobActionKey") in links[i] or note_ids & task_ids
                    or (note.get("jobStep") and note["jobStep"] == step.get("name"))):
                found.append(i)
        comment_matches.append(found)

    result = []
    for i, step in enumerate(steps):
        actions = records(step.get("jobActions") or step.get("actions"))
        def route(record):
            return next((record[k] for k in ("routeResult", "result", "stepResult", "actionResult", "route")
                         if isinstance(record.get(k), str) and record[k].strip()), None)

        outcome = route(step) or next((route(a) for a in reversed(actions) if route(a)), None)
        if not outcome and normalized(step.get("status")) == "completed":
            if normalized(step.get("name")) in REVIEW_STEPS:
                inferred = workflow_decision(steps, i)
                if inferred:
                    outcome = {"Approved": "Approve", "Denied": "Deny"}[inferred] + " (inferred)"
            elif (normalized(step.get("type")) == "start" or
                  normalized(step.get("name")) in {"start", "application start"}):
                next_step = step.get("nextStep")
                if isinstance(next_step, str) and next_step.strip():
                    outcome = next_step + " (next step)"
                elif i + 1 < len(steps) and normalized(steps[i + 1].get("status")) in {"completed", "in progress"}:
                    next_name = text_value(steps[i + 1].get("name"))
                    if next_name:
                        outcome = next_name + " (inferred)"
        time = step.get("timeCreated") or next(
            (a.get("timeActionExecuted") for a in actions if a.get("timeActionExecuted")), None)
        tasks = [task_view(t) for t in mapped[i]]
        notes = comments(step.get("comments")) + comments(
            [n for n, indices in zip(job_comments, comment_matches) if indices == [i]])
        # Some deployments repeat task comments at job level.
        task_notes = [n for task in tasks for n in task["comments"]]
        notes = [n for n in unique_comments(notes) if n not in task_notes]
        result.append({
            "sequence": i + 1, "name": text_value(step.get("name")),
            "status": text_value(step.get("status")), "time": text_value(time),
            "result": text_value(outcome), "tasks": tasks, "comments": notes,
        })
    return {
        "job_reference": text_value(job.get("jobRefNumber")),
        "status": text_value(job.get("status")),
        "steps": result,
        "unassigned_tasks": [task_view(t) for t, indices in zip(txns, matches) if len(indices) != 1],
        "unassigned_comments": unique_comments(comments(
            [n for n, indices in zip(job_comments, comment_matches) if len(indices) != 1])),
    }


def lookup_txns(workspace, code, linked=False):
    # Exact tracking code query avoids the default open-transaction status filter.
    criteria = ["trackingCode = {0}"]
    if linked:
        criteria = ["properties['Link.FnbDashboardTrackingCode'] = {0}",
                    "formStatus IN ('Assigned','Completed','In Progress','Opened','Saved','Submitted','Abandoned','Expired')"]
    response = workspace.session.post(
        workspace.base_url.rstrip("/") + "/secure/api/v1/txn/query",
        json={"scope": "Form", "attributes": TXN_ATTRIBUTES, "fetchLimit": 1000,
              "filters": [{"operator": "and", "criteria": criteria, "params": [code]}]},
        timeout=(10, 60), allow_redirects=False,
    )
    if response.status_code != 200:
        raise WorkspaceReportError(f"Journey Manager transaction lookup failed (HTTP {response.status_code}).")
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("result"), list):
        raise WorkspaceReportError("Journey Manager did not return transaction details.")
    if isinstance(body.get("totalCount"), int) and body["totalCount"] > len(body["result"]):
        raise WorkspaceReportError("Journey Manager returned incomplete related transactions.")
    return records(body["result"]) if linked else [t for t in records(body["result"]) if t.get("trackingCode") == code]


def load_timeline(workspace, code):
    if not workspace.login():
        raise WorkspaceReportError("Journey Manager Workspace sign-in failed.")
    # The initial application's tracking code can itself be the job reference.
    # A task code is resolved via the transaction's job reference instead.
    txns = lookup_txns(workspace, code)
    refs = {code}
    for txn in txns:
        job = txn.get("job")
        ref = job.get("jobRefNumber") if isinstance(job, dict) else None
        if isinstance(ref, str) and CODE.fullmatch(ref):
            refs.add(ref)
    if refs == {code} and not any(isinstance(t.get("job"), dict) and t["job"].get("jobRefNumber") == code for t in txns):
        # Some FNB forms identify the parent application using this existing link property.
        linked = lookup_txns(workspace, code, linked=True)
        for txn in linked:
            job = txn.get("job")
            ref = job.get("jobRefNumber") if isinstance(job, dict) else None
            if isinstance(ref, str) and CODE.fullmatch(ref):
                refs.add(ref)
        seen = {t.get("trackingCode") for t in txns}
        txns.extend(t for t in linked if t.get("trackingCode") not in seen)
    reference_list = ", ".join("'" + ref + "'" for ref in sorted(refs))
    jobs = list(query_jobs(workspace, {
        "attributes": JOB_ATTRIBUTES,
        "filters": [{"operator": "and", "criteria": [f"jobRefNumber IN ({reference_list})"]}],
        "fetchLimit": 10,
    }, "application timeline query"))
    jobs = [j for j in jobs if isinstance(j, dict) and j.get("jobRefNumber") in refs]
    # Do not accidentally combine unrelated workflows.
    actual_refs = refs - {code}
    if actual_refs:
        jobs = [j for j in jobs if j.get("jobRefNumber") in actual_refs]
    if len(jobs) > 1:
        raise WorkspaceReportError("More than one workflow matched this tracking code.")
    if jobs:
        job = jobs[0]
        timeline = build_timeline(job)
        known = {t.get("trackingCode") for t in records(job.get("txns"))}
        timeline["unassigned_tasks"].extend(task_view(t) for t in txns if t.get("trackingCode") not in known)
        return timeline
    if actual_refs:
        raise WorkspaceReportError("The related workflow was not returned by Journey Manager.")
    return {
        "job_reference": None, "status": None, "steps": [],
        "unassigned_tasks": [task_view(t) for t in txns], "unassigned_comments": [],
    }


@timeline_api.after_request
def no_store(response):
    response.headers["Cache-Control"] = "private, no-store"
    return response


@timeline_api.get("/reports/transaction-timeline")
def transaction_timeline():
    msal = request.headers.get("X-MSAL-ID-Token", "").strip()
    if msal:
        authorized = verify_microsoft_token(msal) is not None
    else:
        identity = verify_token(request.headers.get("Authorization")) or {}
        authorized = identity.get("role") in all_groups
    if not authorized:
        return unauthorized()
    code = request.args.get("tracking_code", "").strip()
    if not CODE.fullmatch(code):
        return jsonify(error="A valid tracking code is required."), 400

    from DB import WorkspaceExtract
    workspace = WorkspaceExtract(setup_table=False)
    try:
        return jsonify(load_timeline(workspace, code))
    except Timeout:
        return jsonify(error="Journey Manager timed out. Retry the timeline."), 504
    except WorkspaceReportError as exc:
        return jsonify(error=str(exc)), 502
    except (RequestException, ValueError, TypeError, AttributeError) as exc:
        current_app.logger.warning("Transaction timeline failed: %s", type(exc).__name__)
        return jsonify(error="Journey Manager could not return the application timeline."), 502
    finally:
        if workspace.session is not None:
            workspace.session.close()
