import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import time
import json
from lxml import etree
from dotenv import load_dotenv
import os
import threading
import csv
import re
from DB import SQLConn, Transaction, Customer, Product, insert_unique_jmextract
from collections import defaultdict
from Address import format_address
from collections import defaultdict
from config import get_env_value

load_dotenv(".env")

# Connect to SQL database
def connect_to_db():
    connector = SQLConn()
    connector.connect()
    return connector

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

def get_job(trackingCode, txn_id):
    JM_BASE_URL = get_env_value("JM_BASE_URL")
    job_url =  JM_BASE_URL + '/secure/rest/fluentapi/jobquery/listValues'
    decline_url = JM_BASE_URL + '/secure/rest/fluentapi/txnquery/firstValue'
    
    job_data = {
                "addOrderByAsc": "timeLastProcessed",
                "setReferenceNumber": trackingCode,
                "setFetchLimit": "1",
            }
    job_response = make_request(job_url,job_data)
    reviewDecision = ""
    decline_summary = ''
    if job_response.status_code == 200:
        job_json_obj = job_response.json()
        for job in job_json_obj:
                    for step in job['jobSteps']:
                        reviewDecision = step['name']
                        lastStep = step['name']
                        if step['name'] == 'Decline Application':
                            decline_data = {
                                "setId": f"{txn_id}",
                                "withPropertyMap": True
                            }
                            decline_response = make_request(decline_url,decline_data)
                            if decline_response.status_code == 200:
                                decline_json_obj = decline_response.json()
                                propertyMap = decline_json_obj.get('propertyMap', {})
                                number_of_keys = len(propertyMap)
                                if number_of_keys == 0:
                                    print(f"***    No keys in propertyMap for txn_id: {txn_id}, skipping to next. ***")
                                    continue  # Skip to the next iteration if no keys in propertyMap
                                alloyResponseStr = propertyMap.get('alloy.entitiesComplete.Response', {})
                                alloyResponse = json.loads(alloyResponseStr)
                                embedded = alloyResponse.get('_embedded', {})
                                events = embedded.get('events', [])
                                for event in events:
                                    evaluation_result = event.get('evaluation_result', {})
                                    summary = evaluation_result.get('summary', {})
                                    outcome = summary.get('outcome', {})
                                    if (outcome == 'Denied'):
                                        decline_summary = json.dumps(summary, indent=4)
                                        decline_summary = '"' + decline_summary + '"'
        return {
            "manualReviewDecision" : reviewDecision,
            "declineSummary" : decline_summary,
            "jobs": job_json_obj
        }

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

def getValue(inp,json):
    for key in inp.split("."):
        if not json:
            return None
        json = json.get(key,None)
    return json

def getAdditionalCustomers(txn):
    
    additionalCustomers = getValue("formXml.Root.AvokaSmartForm.Customers.AdditionalCustomers.Customer",txn)
    listOfCustomers = []
    if isinstance(additionalCustomers,dict):
        listOfCustomers = [additionalCustomers]
    elif isinstance(additionalCustomers,list):
        listOfCustomers = additionalCustomers
    
    
    return [customer for customer in listOfCustomers if customer.get("FullName")]

def getDynamicList(obj):
    if isinstance(obj,dict):
        if len(obj.keys()) == 1:
            return [obj[list(obj.keys())[0]]]
        else:
            return [obj]
    elif isinstance(obj,list):
        return obj
    else:
        return []

def getProducts(txn):
    
    products = getDynamicList(
            getValue("formXml.Root.AvokaSmartForm.ShoppingCart.Products",txn)
        )
    
    # TODO: Fix this code
    cleaned_products = []
    for prod in products:
        if isinstance(prod,list):
            for p in prod:
                if p["Product"]:
                    cleaned_products.append(p["Product"])
    if len(cleaned_products) > 0:
        products = cleaned_products
    products = [flatten_dict(product) for product in products]
    crossSellProducts = getDynamicList(getValue("formXml.Root.AvokaSmartForm.ShoppingCart.CrossSellProducts",txn))
    # removedProducts = getDynamicList(getValue("formXml.Root.AvokaSmartForm.ShoppingCart.RemovedProducts",txn))

    listOfProducts = products + crossSellProducts
    
    return [listOfProduct for listOfProduct in listOfProducts if listOfProduct.get("Id")]

def getPromotions(txn):
    promotions = []
    for product in getProducts(txn):
        promotionsNow = getDynamicList(product.get("Promotions",[]))
        for promotion in promotionsNow:
            promotions.append(promotion)
    return [promotion for promotion in promotions if promotion.get("Id",None)]

def get_apps(startDate, endDate):
    start_time = time.time()
    connector = connect_to_db()
    jm_form_codes = get_env_value("JM_FORM_CODE")
    app_list = []
    
    for formCode in jm_form_codes.split(","):
        print(f'    Pulling data for form code {formCode}')
        JM_BASE_URL = get_env_value("JM_BASE_URL")
        txn_url = JM_BASE_URL + '/secure/rest/fluentapi/txnquery/listValues'    
        
        data = {
            "setFormCode": formCode,
            "setFetchLimit": get_env_value("JM_FETCH_TRANSACTION_LIMIT"),
            "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
            "setEndDate": endDate.isoformat() + " MDT",
            "withFormXml": "true"
        }
        
        
        txns_from_jm = 0
        txns_processed = 0
        txn_with_null_content = 0
        txns_saved = 0
        response = make_request(txn_url, data)
        if response.status_code == 200:
            for txn in json.loads(response.text):
                txns_from_jm += 1
                try:
                    print(f"Processing Txn {txn['trackingCode']} that was submitted at {txn['timeSubmitted']}")
                except:
                    pass
                if not txn["formXml"] or not txn["timeSubmitted"]:
                    print(f"Form XML is null for txn id {str(txn['id'])}")
                    txn_with_null_content += 1
                    continue
                
                txns_processed += 1
                root = etree.fromstring(txn["formXml"].encode('utf-8'))
                print("customer_count->"+str(len(list(root.findall(".//Customer")))))
                txn["formXml"] = flatten_dict(xml_dict(root))
                with open(str(txn["id"])+'_myXML.json', 'w') as file:
                    file.write(json.dumps(txn, indent = 2))
                
                avokaSmartForm = getValue("formXml.Root.AvokaSmartForm",txn)
                primaryApplicant = getValue("Customers.Primary",avokaSmartForm)
                if not primaryApplicant:
                    continue
                additionalCustomers = getAdditionalCustomers(txn)
                branch = avokaSmartForm.get("Application",{}).get("Branch",{})
                crossSellProducts = avokaSmartForm.get("ShoppingCart",{}).get("CrossSellProducts",{})
                shoppingCart = avokaSmartForm.get("ShoppingCart",{})
                allProducts = getProducts(txn)
                
                appStatus = "Saved" if txn.get("formStatus","") == "Assigned" or txn.get("formStatus","") == "Opened" or txn.get("formStatus","") == "Saved" else "Abandoned"
                if(appStatus == "Abandoned"):
                    appStatus = "Abandoned:" + str(getValue("SFMData.NarrativeMeta.CurrentPage",avokaSmartForm))
                job = get_job(txn["trackingCode"],txn["id"])
                for jobNow in job["jobs"]:
                    for step in jobNow['jobSteps']:
                        appStatus = step.get("name","")
                # there is no decline smmary for any ... checked in staging and prod 
                if job["declineSummary"]:
                    print("-------------------------------------")
                    print(job)
                    print("-------------------------------------")
                # had to add total funding amount 
                ret_data = {
                    "tId": txn["id"],
                    "eCATrackingCode": txn["trackingCode"],
                    "appStartDate": txn["timeCreated"],
                    "appSubmitDate": txn["timeSubmitted"],
                    "appUpdateDate": txn["timeUserLastModified"],
                    "JMAppStatus": appStatus,
                    "manualReviewDecision": job.get("manualReviewDecision",""), # Commented
                    # the values for product set id, alloy decision and total funding product - are encypted
                    "alloyDecision": job.get("declineSummary",""),
                    "primaryApplicantName": getValue("FullName", primaryApplicant), #primaryApplicant.get("FullName",""),
                    "primaryApplicantSSN": getValue("LastFourSsn", primaryApplicant), #primaryApplicant.get("LastFourSsn",""),
                    "mobile": getValue("PhoneNumber", primaryApplicant), # primaryApplicant.get("PhoneNumber",""),
                    "primaryCurrentAddress": getValue("AddressCurrent", primaryApplicant),
                    "primaryEmail": getValue("emailAddress", primaryApplicant),
                    "customerType": "Existing" if primaryApplicant.get("IsCurrentCustomer", "false") == "true"or primaryApplicant.get("IsCurrentCustomerShoppingCart", "false") == "true" else "New",
                    "numCoApplicants": len(additionalCustomers),             
                    "promotions": " | ".join([promotion for promotion in getPromotions(txn)]),
                    "coApplicantsNames": [customer.get("FullName") for customer in additionalCustomers if customer.get("FullName")],
                    "coApplicantsSSNs": [customer.get("Tin") for customer in additionalCustomers if customer.get("Tin")],
                    "firstProduct": allProducts[0].get("Id",""),
                    "products": " | ".join([product.get("Name","") for product in allProducts if product and product.get("Name")]),
                    "countOfDepositProducts": len([product.get("Id") for product in allProducts if product.get("Type","") == "savings" or product.get("Type","") == "checking" or product.get("Type","") == "certificate of deposit" or product.get("Type","") == "special certificate of deposit"]),
                    "countOfLendingProducts": len([product.get("Id") for product in allProducts if product.get("Type","") == "000"]),
                    "payment": avokaSmartForm.get("Payment",{}).get("FundingAccountUsed",{}).get("PaymentMethod",""),
                    "totalAmountToFund": shoppingCart.get("TotalAmountToFund",""),
                    "promoCodes": getValue("formXml.Root.AvokaSmartForm.Application.PromoCode",txn),
                    "CrossSellProducts": " | ".join([f"{cSProduct.get('Id')}: {cSProduct.get('Name')}" for cSProduct in getDynamicList(getValue("formXml.Root.AvokaSmartForm.ShoppingCart.CrossSellProducts",txn)) if cSProduct.get("Id")]),
                    # If customer selected a crossSellProduct -> Opted = Y else Opted = N
                    "Opted": 'Y' if getValue("CrossSellProduct",crossSellProducts) != None else 'N',
                    "BranchID": branch.get("Id",""),
                    "BranchContactPerson": branch.get("Name",""),
                    "BranchContactPhone": branch.get("PhoneNumber",""),
                    "_json_customers": [primaryApplicant] + additionalCustomers,
                    "_json_products_details": allProducts
                }
                app_list.append(ret_data)
                try:
                    save_to_db(ret_data, connector)
                    txns_saved += 1
                except Exception as e:
                    print("There was an error saving txn. ^^" , e)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"        Number of txns: {txns_from_jm}, "
              f"Number of txns processed: {txns_processed}, "
              f"Number of txns with null: {txn_with_null_content}, "
              f"Number of txns saved: {txns_saved}, "
              f"Elapsed time: {elapsed_time} seconds")
        
    connector.disconnect()
    return app_list

def save_to_db(txn, connector):


    fin = {
        "tId": None,
        "eCATrackingCode": txn["eCATrackingCode"],
        "eCAID": txn["tId"],
        "CustomerID": 0,
        "AppStartDate": txn["appStartDate"],
        "AppSubmitDate": txn["appSubmitDate"],
        "AppUpdateDate": txn["appUpdateDate"],
        "AppStatus": txn["JMAppStatus"],
        "DeclineReason": txn["alloyDecision"],
        "PrimaryName": txn["primaryApplicantName"],
        "PrimarySSN": txn["primaryApplicantSSN"],
        "NewCustomer": txn["customerType"],
        "NumCoApplicant": txn["numCoApplicants"],
        "ProductSetId": txn["products"],
        "NumDepositProducts": txn["countOfDepositProducts"],
        "NumLendingProducts": txn["countOfLendingProducts"],
        "FundingMethod": txn["payment"],
        "TotalFundingAmount": txn["totalAmountToFund"],
         "CrossSellProducts": txn["CrossSellProducts"],
         "Opted": txn["Opted"],
        "UnderWriterStatus1": "",
        "UnderWriterStatus2": "",
        "BranchID": txn["BranchID"], 
        "BranchContactPerson": txn["BranchContactPerson"],
        "BranchContactPhone": txn["BranchContactPhone"],
        "Promotions": txn["promotions"],
        "PromoCodes": txn["promoCodes"]
    }
    for key,value in fin.items():
        if value:
            fin[key] = str(value).encode("ascii", errors="ignore").decode("ascii")
    if connector.connection: 
        
        transactionDB = Transaction(connector)

        connector.execute(
            f"DELETE FROM [DigitalReport].[dbo].[Transactions] WHERE eCATrackingCode = '{txn['eCATrackingCode']}'"
        )

        transaction_message = transactionDB.create_transaction_from_json(fin)
        tid = transaction_message.get("tId")
        if tid == None:
            return
        if(tid >= 0):
            customer_obj = Customer(connector)
            for customer in txn["_json_customers"]:
                customer["tId"] = tid
                customer_obj.save_customer(customer)
            products_obj = Product(connector)
            for product in txn["_json_products_details"]:
                if product:
                    products_obj.save_product(product)

def sanitize_json_string(json_string): 
    # Remove control characters that are not valid in JSON
    sanitized_string = re.sub(r'[\x00-\x1F\x7F]', '', json_string)
    return sanitized_string
# _________________________________________________________________________

def long_running_function(start_date, end_date):
    date_format = "%Y-%m-%d"
    # start_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)
    print(f"Fetching data from {start_date} to {end_date}")
    get_apps(start_date,end_date)
    print(f"Function completed from {start_date} to {end_date}")

def fetch_async(start_date, end_date):
    last_run_time = read_last_run_time()
    now = datetime.now()

    if last_run_time is None or now - last_run_time > timedelta(hours=2):
        write_last_run_time()
        def wrapper():
            long_running_function(start_date, end_date)

        thread = threading.Thread(target=wrapper)
        thread.daemon = True  # Set the thread as a daemon thread
        thread.start()
    else:
        print(f"Function not called. Last run was at {last_run_time}")

LAST_RUN_FILE = 'last_run_time.txt'

def write_last_run_time():
    with open(LAST_RUN_FILE, 'w') as file:
        file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def read_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as file:
            last_run_time_str = file.read().strip()
            if last_run_time_str:
                return datetime.strptime(last_run_time_str, '%Y-%m-%d %H:%M:%S')
    return None


def update_JMExtract(sql,trackingCode):
    import sys
    startDate = datetime.now() - timedelta(days=30)
    endDate = datetime.now()

    


    resp = make_request(get_env_value("JM_BASE_URL")+'/secure/rest/fluentapi/txnquery/listValues', data = {
                "setFetchLimit": "1",
                #"setFormCode": "fnb-consumer",
                "setTrackingCode": trackingCode,
                "setStartDate": startDate.isoformat().split(".")[0] + " MDT",
                "setEndDate": endDate.isoformat().split(".")[0] + " MDT",
                "withFormXml": "true"
            }, retries=1, delay=2)
    
    

    if resp.status_code == 200:
        if len(json.loads(resp.text)) == 0:
            sys.stdout.write(f" - No txn in the list")
        for txn in json.loads(resp.text):
            if not txn["formXml"] or txn["formXml"] == "":
                sys.stdout.write(f" - XML is missing ")
                continue
            sys.stdout.write(f" - XML found")
            root = etree.fromstring(txn["formXml"].encode('utf-8'))
            to_insert = json.dumps(xml_dict(root).get("Root")).replace("'", "%27")
            prefix_sql = "Insert into [DigitalReport].[dbo].[JMExtract] ( tID, LoadDateTime, RawData) Values "
            sql.execute(prefix_sql + f"('{trackingCode}', CURRENT_TIMESTAMP, '{to_insert}')")
            sys.stdout.write(f" - Extract Pulled")
    else:
        # Insert a blank response for formXml
        prefix_sql = "Insert into [DigitalReport].[dbo].[JMExtract] ( tID, LoadDateTime, RawData) Values "
        sql.execute(prefix_sql + f"('{trackingCode}', CURRENT_TIMESTAMP, '')")
        print(f"Error fetching data for trackingCode {trackingCode}: {resp.status_code} - {resp.text}")

    
