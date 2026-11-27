"""Read-only, on-demand application timeline from Journey Manager Workspaces."""
import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from requests import RequestException, Timeout

from authentication import unauthorized, verify_microsoft_token, verify_token
from role_filter import all_groups
from report_modules.manual_review import WorkspaceReportError, query_jobs

timeline_api = Blueprint("transaction_timeline", __name__)
CODE = re.compile(r"[A-Za-z0-9_-]{1,128}")
JOB_ATTRIBUTES = ["jobRefNumber", "status", "steps", "comments", "txns", "txns.comments"]
TXN_ATTRIBUTES = ["trackingCode", "submitKey", "job", "job.jobRefNumber", "formName", "formStatus",
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


def event_time(value):
    if not isinstance(value, str):
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else datetime.min.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def build_timeline(job):
    """One entry per related transaction, with its actual comments.

    Workflow steps are not displayed or inferred. Use explicit comment identifiers
    only; comments without a proven transaction owner remain application notes.
    """
    txns = [dict(t) for t in records(job.get("txns"))]
    notes = records(job.get("comments"))
    actions = [a for step in records(job.get("steps"))
               for a in records(step.get("jobActions") or step.get("actions"))]
    for step in records(job.get("steps")):
        notes.extend(records(step.get("comments")))
    application_notes = []
    for note in notes:
        ids = identifiers(note)
        key = note.get("jobActionKey")
        matching_actions = [a for a in actions if key and a.get("jobActionKey") == key]
        owners = [t for t in txns if ids & identifiers(t)
                  or (key and key == t.get("jobActionKey"))
                  or action_matches(t, matching_actions)]
        if len(owners) == 1:
            txn = owners[0]
            txn["comments"] = unique_comments(records(txn.get("comments")) + [note])
        else:
            application_notes.append(note)

    transactions = [task_view(t) for t in txns]
    for txn in transactions:
        txn["comments"] = unique_comments(txn["comments"])
        txn["comments"].sort(key=lambda n: event_time(n["time"]), reverse=True)
    transactions.sort(key=lambda t: event_time(t["created"] or t["updated"]), reverse=True)
    existing_notes = [n for txn in transactions for n in txn["comments"]]
    application_notes = [n for n in unique_comments(comments(application_notes)) if n not in existing_notes]
    application_notes.sort(key=lambda n: event_time(n["time"]), reverse=True)
    return {
        "job_reference": text_value(job.get("jobRefNumber")),
        "status": text_value(job.get("status")),
        "transactions": transactions,
        "application_comments": application_notes,
    }


def transaction_ref(txn):
    job = txn.get("job")
    return (job.get("jobRefNumber") if isinstance(job, dict) else None) or txn.get("jobRefNumber")


def merge_job_transactions(job, additional, action_records=()):
    """Combine proven job members, preserving comments and identifiers."""
    ref = job.get("jobRefNumber")
    txns = [dict(t) for t in records(job.get("txns"))]
    for txn in additional:
        ids = identifiers(txn)
        matches = [i for i, existing in enumerate(txns) if ids & identifiers(existing)]
        if transaction_ref(txn) not in (None, ref):
            continue
        if len(matches) == 1:
            target = txns[matches[0]]
            # A contradictory identifier is not safe to merge.
            if any(target.get(k) and txn.get(k) and target[k] != txn[k]
                   for k in ("submitKey", "trackingCode")):
                continue
            for key, value in txn.items():
                if key == "comments":
                    target[key] = unique_comments(records(target.get(key)) + records(value))
                elif not target.get(key) and value:
                    target[key] = value
        elif not matches and (transaction_ref(txn) == ref or txn.get("trackingCode") == ref
                              or any(action_matches(txn, actions) for actions in action_records)):
            txns.append(dict(txn))
    return txns


def missing_submission_keys(job, txns):
    known = set().union(*(identifiers(t) for t in txns))
    missing = set()
    for step in records(job.get("steps")):
        for action in records(step.get("jobActions") or step.get("actions")):
            value = action.get("submission")
            if isinstance(value, dict):
                value = value.get("submitKey")
            if isinstance(value, str) and CODE.fullmatch(value) and value not in known:
                missing.add(value)
    return sorted(missing)


def lookup_submissions(workspace, keys):
    """Resolve missing action submissions directly using the documented submitKey filter."""
    results = []
    for offset in range(0, len(keys), 50):
        batch = keys[offset:offset + 50]
        values = ", ".join("'" + key + "'" for key in batch)
        response = workspace.session.post(
            workspace.base_url.rstrip("/") + "/secure/api/v1/txn/query",
            json={"scope": "Form", "attributes": TXN_ATTRIBUTES, "fetchLimit": len(batch),
                  "filters": [{"operator": "and", "criteria": [f"submitKey IN ({values})"]}]},
            timeout=(10, 60), allow_redirects=False,
        )
        if response.status_code != 200:
            raise WorkspaceReportError(f"Journey Manager submission lookup failed (HTTP {response.status_code}).")
        body = response.json()
        if not isinstance(body, dict) or not isinstance(body.get("result"), list):
            raise WorkspaceReportError("Journey Manager did not return submission details.")
        if isinstance(body.get("totalCount"), int) and body["totalCount"] > len(body["result"]):
            raise WorkspaceReportError("Journey Manager returned incomplete submission details.")
        results.extend(t for t in records(body["result"]) if t.get("submitKey") in batch)
    return results


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
        ref = transaction_ref(txn)
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
        job = dict(jobs[0])
        actions = [records(s.get("jobActions") or s.get("actions")) for s in records(job.get("steps"))]
        job["txns"] = merge_job_transactions(job, txns, actions)
        missing = missing_submission_keys(job, job["txns"])
        if missing:
            resolved = lookup_submissions(workspace, missing)
            job["txns"] = merge_job_transactions(job, resolved, actions)
        return build_timeline(job)
    if actual_refs:
        raise WorkspaceReportError("The related workflow was not returned by Journey Manager.")
    return build_timeline({"txns": txns})


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
