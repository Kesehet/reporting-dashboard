"""Journey Manager XML retrieval and safe RawData storage."""
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta

import requests
from lxml import etree
from requests.auth import HTTPBasicAuth

from config import get_env_value
from jm_endpoints import jm_fluent_base_url, JM_RETENTION_DAYS


def make_request(url, data, retries=2, delay=2, debug=False):
    username = get_env_value("REACT_APP_JOURNEY_MANAGER_USER")
    password = get_env_value("REACT_APP_JOURNEY_MANAGER_PASSWORD")
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.post(
                url, json=data, auth=HTTPBasicAuth(username, password),
                timeout=(10, 60),
            )
            if response.status_code in (408, 429, 500, 502, 503, 504) and attempt + 1 < retries:
                time.sleep(delay)
                continue
            return response
        except requests.RequestException as exc:
            last_error = exc
            if debug:
                print(f"Journey Manager request attempt {attempt + 1} failed: {type(exc).__name__}")
            if attempt + 1 < retries:
                time.sleep(delay)
    raise RuntimeError(
        f"Journey Manager request failed after {retries} attempts"
    ) from last_error


def xml_dict(element):
    result = defaultdict(list)
    for child in element:
        child_dict = xml_dict(child)
        if child.tag in result:
            if isinstance(result[child.tag], list):
                result[child.tag].append(child_dict or child.text)
            else:
                result[child.tag] = [result[child.tag], child_dict or child.text]
        else:
            result[child.tag] = child_dict or child.text
    return {element.tag: flatten_dict(dict(result))} if result else element.text


def flatten_dict(d):
    if isinstance(d, dict):
        for key, value in list(d.items()):
            if value is not None and isinstance(value, dict) and len(value) == 1:
                child_key, child_value = next(iter(value.items()))
                if key in child_key:
                    d[key] = child_value
            if isinstance(value, list):
                for item in value:
                    flatten_dict(item)
            elif isinstance(value, dict):
                flatten_dict(value)
    return d


def _store_xml(sql, tracking_code, raw_data):
    """Fill missing payloads or insert a new row; never replace nonempty RawData."""
    if not sql.connection:
        raise RuntimeError("No SQL connection available for Journey Manager extraction")
    cursor = sql.connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE [DigitalReport].[dbo].[JMExtract]
               SET RawData = ?, LoadDateTime = CURRENT_TIMESTAMP
             WHERE tID = ?
               AND (RawData IS NULL OR LTRIM(RTRIM(RawData)) IN ('', 'null'))
            """,
            (raw_data, tracking_code),
        )
        updated = cursor.rowcount
        inserted = 0
        if updated == 0:
            cursor.execute(
                """
                INSERT INTO [DigitalReport].[dbo].[JMExtract] (tID, LoadDateTime, RawData)
                SELECT ?, CURRENT_TIMESTAMP, ?
                 WHERE NOT EXISTS (
                       SELECT 1 FROM [DigitalReport].[dbo].[JMExtract] WITH (UPDLOCK, HOLDLOCK)
                        WHERE tID = ?
                 )
                """,
                (tracking_code, raw_data, tracking_code),
            )
            inserted = cursor.rowcount
        sql.connection.commit()
        return updated > 0 or inserted > 0
    except Exception:
        sql.connection.rollback()
        raise
    finally:
        cursor.close()


def update_JMExtract(sql, trackingCode, *, report_error=None):
    """Return True only when nonempty, valid XML was persisted successfully."""
    def failure(message):
        if report_error is None:
            print(message)
        else:
            report_error(message)
        return False

    if not trackingCode or not str(trackingCode).strip():
        return failure("Missing Journey Manager tracking code.")
    if not sql.connection:
        return failure("Reporting database connection unavailable.")

    start_date = datetime.now() - timedelta(days=JM_RETENTION_DAYS)
    end_date = datetime.now()
    try:
        url = jm_fluent_base_url() + "/txnquery/listValues"
        response = make_request(url, data={
            "setFetchLimit": "1",
            "setTrackingCode": trackingCode,
            "setStartDate": start_date.isoformat().split(".")[0] + " MDT",
            "setEndDate": end_date.isoformat().split(".")[0] + " MDT",
            "withFormXml": "true",
        })
    except Exception:
        return failure("Journey Manager request failed.")

    if response.status_code != 200:
        return failure(f"Journey Manager returned HTTP {response.status_code}.")

    try:
        data = json.loads(response.text)
    except (TypeError, ValueError):
        return failure("Journey Manager returned invalid JSON.")

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        return failure("Journey Manager returned no transactions.")

    for txn in data:
        if not isinstance(txn, dict) or not txn.get("formXml"):
            continue
        try:
            root = etree.fromstring(txn["formXml"].encode("utf-8"))
            parsed = xml_dict(root).get("Root")
            if not isinstance(parsed, (dict, list)) or not parsed:
                continue
            raw_data = json.dumps(parsed, ensure_ascii=False)
            _store_xml(sql, trackingCode, raw_data)
            return True
        except (ValueError, TypeError, etree.XMLSyntaxError):
            continue
        except Exception:
            return failure("Could not save the Journey Manager extract.")

    return failure("Journey Manager returned no usable form XML.")
