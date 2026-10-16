import os
import json
metrics_filename = "metrics.json"
def update_metrics(key,value):

    if os.path.exists(metrics_filename):
        with open(metrics_filename, "r") as f:
            try:
                
                metrics = json.load(f)
            except json.JSONDecodeError:
                metrics = {}
    else:
        metrics = {}
    
    metrics[key] = value

    with open(metrics_filename,"w") as f:
        json.dump(metrics, f , indent=4)
   
def get_metrics():
    val = ""
    with open(metrics_filename,"r") as f:
        val = json.load(f)
    return val

def update_metrics_from_sql(key, txn, query):
    resp = txn.get_transactions_by_sql_query(query)
    if type(resp) == list and len(resp) > 0 and len(resp[0].keys()) == 1:
        ret = []
        col = list(resp[0].keys())[0]
        for res in resp:
            ret.append(res.get(col))
        resp = ret
    update_metrics(key, resp)