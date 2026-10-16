import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import time
import json
from lxml import etree
from config import get_env_value
from collections import defaultdict

# Make a request to the given URL with data and return the response
def make_request(url, data, retries=3, delay=2, debug = False):
    username = get_env_value("REACT_APP_JOURNEY_MANAGER_USER")
    password = get_env_value("REACT_APP_JOURNEY_MANAGER_PASSWORD")
    for attempt in range(retries):
        try:
            return requests.post(url, json=data, auth=HTTPBasicAuth(username, password))
        except Exception as e:
            if debug:
                print(f"Error calling url: {url}. Attempt {attempt + 1} of {retries}. Error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return {"error": e, "url": url, "data": data}

# _________________________________________________________________________

# Function to convert XML to dictionary
def xml_dict(element):
    result = defaultdict(list)
    for child in element:
        child_dict = xml_dict(child)
        if child.tag in result:
            # Append to the existing list if the tag already exists
            if isinstance(result[child.tag], list):
                result[child.tag].append(child_dict or child.text)
            else:
                result[child.tag] = [result[child.tag], child_dict or child.text]
        else:
            # Initialize a list for repeated tags
            result[child.tag] = child_dict or child.text
    return {element.tag: flatten_dict(dict(result))} if result else element.text


def flatten_dict(d):
    if isinstance(d,dict):
        for key,value in list(d.items()):
                       
            if not value == None and isinstance(value, dict) and len(value) == 1 :
                child_key, child_value = next(iter(value.items()))
                if key in child_key:
                    d[key] = child_value 
            if isinstance(value, list):
                for item in value:
                    flatten_dict(item)
            elif isinstance(value, dict):
                flatten_dict(value)
    return d



def update_JMExtract(sql,trackingCode):
    import sys
    startDate = datetime.now() - timedelta(days=30)
    endDate = datetime.now()

    resp = make_request(get_env_value("JM_BASE_URL") + '/manager/secure/rest/fluentapi/txnquery/listValues', data={
        "setFetchLimit": "1",
        #"setFormCode": "fnb-consumer",
        "setTrackingCode": trackingCode,
        "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
        "setEndDate": endDate.isoformat().split(".")[0] + " MDT",
        "withFormXml": "true"
    }, retries=1, delay=2)

    # Handle network/errors where make_request returned an error dict
    if not hasattr(resp, 'status_code'):
        prefix_sql = "Insert into [DigitalReport].[dbo].[JMExtract] ( tID, LoadDateTime, RawData) Values "
        sql.execute(prefix_sql + f"('{trackingCode}', CURRENT_TIMESTAMP, '')")
        print(f"Error making request for trackingCode {trackingCode}: {resp}")
        return

    # Parse JSON safely and ensure we iterate over a list
    try:
        data = json.loads(resp.text)
    except Exception:
        data = []

    if resp.status_code == 200:
        if not isinstance(data, list):
            if not data:
                sys.stdout.write(f" - No txn in the list")
                return
            # if a single object is returned, wrap it in a list
            if isinstance(data, dict):
                data = [data]
            else:
                # unexpected non-iterable JSON (e.g. a number)
                sys.stdout.write(f" - Unexpected response format: {type(data)}")
                return

        if len(data) == 0:
            sys.stdout.write(f" - No txn in the list")
            return

        for txn in data:
            if not txn or not txn.get("formXml"):
                sys.stdout.write(f" - XML is missing ")
                continue
            sys.stdout.write(f" - XML found")
            try:
                root = etree.fromstring(txn["formXml"].encode('utf-8'))
            except Exception:
                sys.stdout.write(f" - Failed to parse XML")
                continue
            to_insert = json.dumps(xml_dict(root).get("Root")).replace("'", "%27")
            prefix_sql = "Insert into [DigitalReport].[dbo].[JMExtract] ( tID, LoadDateTime, RawData) Values "
            sql.execute(prefix_sql + f"('{trackingCode}', CURRENT_TIMESTAMP, '{to_insert}')")
            sys.stdout.write(f" - Extract Pulled")
    else:
        # Insert a blank response for formXml on non-200
        prefix_sql = "Insert into [DigitalReport].[dbo].[JMExtract] ( tID, LoadDateTime, RawData) Values "
        sql.execute(prefix_sql + f"('{trackingCode}', CURRENT_TIMESTAMP, '')")
        print(f"Error fetching data for trackingCode {trackingCode}: {resp.status_code} - {getattr(resp, 'text', repr(resp))}")

    