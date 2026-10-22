from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional
from cache_manager import get_cached_item, set_cached_item, clear_all_cache,  cached_date_list
from utils import *
import json
import os
from time import time
from typing import Any, Dict, Optional
import hashlib
import requests
from requests.auth import HTTPBasicAuth
from config import get_env_value
from jm_endpoints import jm_fluent_base_url


class FluentAPIBase:
    """Small reusable client for TJM Fluent API REST endpoints."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 600,
    ) -> None:
        self.base_url = jm_fluent_base_url(base_url)
        self.username = username or os.getenv("TJM_USERNAME") or os.getenv("FLUENT_API_USERNAME")
        self.password = password or os.getenv("TJM_PASSWORD") or os.getenv("FLUENT_API_PASSWORD")
        
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self._auth_retry_count = 0



    def make_request(self, url, data, retries=3, delay=2, debug = False, method="POST", is_fluent_api=True):
        
        url = self.base_url + url
        if not is_fluent_api:
            url = url.replace("/fluentapi","")

        cache_dir = "jm_cache"     
        os.makedirs(cache_dir, exist_ok=True)
        
        filepath = f"{cache_dir}/"+hashlib.sha256("_".join(f"{key}-{value}" for key, value in data.items()).encode() ).hexdigest()+ ".json"

        if os.path.exists(filepath):         
            if debug:             
                print(f"Loading cached response: {filepath}")         

            with open(filepath, "r", encoding="utf-8") as f:
                try:             
                    return json.load(f)
                except:
                    pass
        else:
            if debug:
                print(f"{filepath}")

        for attempt in range(retries):
            try:
                
                if method == "POST":
                    r = self.session.post(url, json=data, timeout=self.timeout).text
                if method == "GET":
                    r = self.session.get(url, json=data, timeout=self.timeout).text
                    
                if debug:
                    print("Response from Server", r)

                r = json.loads(r)

                with open(filepath, "w", encoding="utf-8") as f:               
                    json.dump(r, f, indent=2)
                
                return r
                
            except Exception as e:
                if debug:
                    print(f"Error calling url: {url}. Attempt {attempt + 1} of {retries}. Error: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    return {"error": e, "url": url, "data": data}

    

class TransactionSearchError(RuntimeError):
    pass


class FluentAPITransactionSearch:
    def __init__(self, client: Optional[FluentAPIBase] = None) -> None:
        self.client = client or FluentAPIBase(
            base_url=jm_fluent_base_url(),
            username=get_env_value("REACT_APP_JOURNEY_MANAGER_USER") or os.getenv("REACT_APP_JOURNEY_MANAGER_USER"),
            password=get_env_value("REACT_APP_JOURNEY_MANAGER_PASSWORD") or os.getenv("REACT_APP_JOURNEY_MANAGER_PASSWORD"),
        )

    def search_txn(self, 
                   tracking_code: str, 
                   start_date: str, 
                   end_date: str,
                   form_code: str,
                   just_tracking_code: bool,
                   full_response: bool
                   ) -> Dict[str, Any]:
            
        all_possible_results = []
        intervals = get_list_of_days_between(start_date, end_date)
        for interval in intervals:
            if isinstance(interval['start_date'], datetime):
                start_dt = interval['start_date']
            else:
                start_dt = datetime.strptime(interval['start_date'], "%Y-%m-%d") if interval['start_date'] else datetime.now()

            if isinstance(interval['end_date'], datetime):
                end_dt = interval['end_date']
            else:
                end_dt = datetime.strptime(interval['end_date'], "%Y-%m-%d") if interval['end_date'] else datetime.now()

            startDate = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            endDate = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)



            base_payload = {
                "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
                "setEndDate": endDate.isoformat().split(".")[0] + " MDT",
                "withFormXml": "true",
            }
            if tracking_code:            
                base_payload["setTrackingCode"] = tracking_code
                base_payload["setFetchLimit"] = "1"
            else:
                base_payload["setFormCode"] = form_code
                base_payload["setFetchLimit"] = "100"
                base_payload["hasProperty"] = "Fatal Error"

            direct_payloads = self.client.make_request(
                '/txnquery/listValues', data =base_payload , retries=1, delay=2
                )

            indirect_payloads = self.client.make_request(
                        '/txnquery/listValues', data ={
                                "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
                                "setEndDate": endDate.isoformat().split(".")[0] + " MDT",
                                "withFormXml": "true",
                                "setFormStatus": "Abandoned",
                                "setFormCode": form_code
                            } , retries=1, delay=2
                        )

            saved_payloads = self.client.make_request(
                                '/txnquery/listValues', data ={
                                        "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
                                        "setEndDate": endDate.isoformat().split(".")[0] + " MDT",
                                        "withFormXml": "true",
                                        "setFormStatus": "Saved",
                                        "setFormCode": form_code
                                    } , retries=1, delay=2
                                )
            

            if len(direct_payloads) == 0:
                continue

            if isinstance(indirect_payloads, dict) != 0:
                direct_payloads.update(indirect_payloads)

            if isinstance(saved_payloads, dict):
                direct_payloads.update(saved_payloads)

            if len(direct_payloads) == 0:
                continue

            

        
            for txn in direct_payloads:
                if not isinstance(txn, dict):
                    print(txn)
                    continue
                txn_id = txn.get("id")

                if not txn_id:
                    raise TransactionSearchError("Transaction payload did not include an id")

                result: Dict[str, Any] = {
                    "transaction": txn,
                    "properties": {},
                }

                
                property_response = self.client.make_request(
                    '/txnquery/firstValue', 
                    data = {"setId": str(txn_id), "withPropertyMap": True}, retries=1, delay=2)
                
                result["properties"] = property_response.get("propertyMap",{})

                result["isBankerAssisted"] = result.get("properties",{}).get("isBankerAssisted", "")
                result["Start Date"] = result.get("transaction",{}).get("timeCreated", "")
                result["Associated Tracking Codes"] = ', '.join(list(json.loads(result.get("properties",{}).get("FormInfoMap", "{}")).keys()))
                result["Form Name"] = result.get("transaction",{}).get("formName", "")


                form_xml = result.get("transaction", {}).get("formXml") or ""
    
                result["CurrentPage"] = (
                    form_xml.split("CurrentPage>", 1)[1].split("</CurrentPage", 1)[0].replace("</", "")
                    if "CurrentPage>" in form_xml and "</CurrentPage" in form_xml
                    else None
                )



                is_error = False
                error_now = ""
                # Find any key that starts or contains the word Error
                for p in result["properties"].keys():
                    if "fatal error" in str(p).lower():
                        error_now = result["properties"].get(str(p))
                        print(f"{p}: Contains Error ! \n {error_now}")
                        print("-------------------------")
                        is_error = True
                        break
                
                result["is_error"] = is_error
                result['error'] = error_now
                result["tracking_code"] = result.get("transaction",{}).get("trackingCode", "Missing tracking code")

                

                result["aa_call"] = self.client.make_request(
                        f'/transactions/v1/{txn_id}', method="GET", retries=1, delay=2, data={}, debug=False, is_fluent_api=False
                    )
                
                result["submissionGroupNames"] = result["aa_call"].get("submissionGroupNames", "")
                result["Form Status"] = result.get("transaction",{}).get("formStatus", "Missing Form Status")
                
                if full_response:
                    job_payload = {
                        "addOrderByAsc": "timeLastProcessed",
                        "setReferenceNumber": tracking_code,
                        "setFetchLimit": "1",
                    }
                    job_response = self.client.make_request(
                            '/jobquery/listValues',
                            data =job_payload, retries=1, delay=2)
                    result["job_query"] = job_response
                        
                
                if not full_response:
                    del result["properties"]
                    del result["transaction"]
                    del result["aa_call"]

                
                all_possible_results.append(result)
        if just_tracking_code:
            return list(set([t.get("trackingCode", "") for t in all_possible_results if isinstance(t, dict) ]))
        
        return all_possible_results


def search_txn(params: Dict, start_date: str, end_date: str, just_tracking_code:bool) -> Dict[str, Any]:
    searcher = FluentAPITransactionSearch()
    tracking_codes = params.get("tracking_codes","").replace(" ", "").split(",")
    if not tracking_codes or tracking_codes == "":
        tracking_codes = ['']
    form_code = params.get("form_code", "fnb-consumer")
    full_response = params.get("full_response", False)
    result = []
    for tracking_code in tracking_codes:
        result.append(
            searcher.search_txn(tracking_code, start_date, end_date, form_code, just_tracking_code, full_response)
        )
        # with open(f".cache_requests/{tracking_code}_cached.json", "w") as f:
        #     f.write(json.dumps(searcher.search_txn(tracking_code, start_date, end_date, form_code, just_tracking_code, full_response=True), indent=4))
    
    if just_tracking_code:
        return result
    
    final_result = []
    for r in result:
        for s in r:
            final_result.append(s)
    if len(final_result) == 0:
        return {
            "headers" : ["-"],
            "rows" : [["No txns found"]]
        }
    return {
        "headers": list(final_result[0].keys()),
        "rows": [list(item.values()) for item in  final_result ]
    }
    



    
