from ldap3 import Server, Connection, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES
from ldap3.core.exceptions import LDAPException
from flask import Flask, request, jsonify, abort, render_template_string
from flask_cors import CORS
from datetime import timedelta, datetime
import jwt
import os
from dotenv import load_dotenv
from application import fetch_async
from DB import SQLConn, Transaction
from role_filter import role_filter as rf
from role_filter import get_role
from waitress import serve
import threading
import sched
import time
from charts import getChartData, get_request_dict
import traceback
from cache_manager import get_cached_item, set_cached_item, clear_all_cache, get_cached_chart_data, cached_date_list
from upload_csv import UPLOAD_FORM_HTML, beautify_response
from config import get_env_value
from metrics import update_metrics, get_metrics
from helper.chat_serve import _INFLIGHT_LOCK, _INFLIGHT, _chart_key, _acquire_or_wait_for_slot
from urllib.parse import urlencode


scheduler = sched.scheduler(time.time, time.sleep)
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = get_env_value('RELAY_SERVER_SECRET')
CORS(app)
CSV_FOLDER_REPORT = 'uploads/report'
CSV_FOLDER_REPORTS = 'uploads/reports'

if os.path.exists(CSV_FOLDER_REPORT):
    CSV_FOLDER = CSV_FOLDER_REPORT
elif os.path.exists(CSV_FOLDER_REPORTS):
    CSV_FOLDER = CSV_FOLDER_REPORTS
else:
    CSV_FOLDER = CSV_FOLDER_REPORTS
    os.makedirs(CSV_FOLDER, exist_ok=True)
    print(f"CSV folder not found. Created folder: {CSV_FOLDER}")

print(f"Using CSV folder: {CSV_FOLDER}")
app.config['CSV_FOLDER'] = CSV_FOLDER
# the move it process is in progress - the CSV folder gets active after the process is done

INTERNAL_CSV_FOLDER = 'uploads/csv'
os.makedirs(INTERNAL_CSV_FOLDER, exist_ok=True)
app.config['INTERNAL_CSV_FOLDER'] = INTERNAL_CSV_FOLDER

@app.route('/', methods=['GET', 'POST'])
def get_all_between_dates():
    token = request.headers.get('Authorization')
    if token is None:
        abort(400, description="Please provide a token")
    payload = verify_token(token)
    if payload is None:
        abort(400, description="Invalid token")
    date_format = "%Y-%m-%d"
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        abort(400, description="Please provide both start_date and end_date")
    
    key = f"All_Transactions_between_{start_date}_and_{end_date}"

    
    
    cached_data = get_cached_item(key)
    if cached_data:
        return jsonify(cached_data), 200
    
    try:
        start_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)
    except ValueError:
        abort(400, description="Invalid date format. Please use YYYY-MM-DD.")
    
    connection = SQLConn()
    connection.connect()
    transaction = Transaction(connection)
    resp = transaction.get_transactions_by_date_range(start_date, end_date)
    set_cached_item(resp, key)
    connection.disconnect()
    
    return rf(resp, payload["role"])




# Set to track unique URLs
logged_urls = set()
LOG_FILE = "logged_chart_urls.txt"

def log_unique_url(name, params):
    today = datetime.today()

    for key in ["start_date", "end_date"]:
        if key in params:
            try:
                param_date = datetime.strptime(params[key], "%Y-%m-%d")
                offset_days = (param_date - today).days
                params[key] = f"__OFFSET_{offset_days}__"
            except ValueError:
                pass  # Leave as-is if not a valid date

    base_url = f"/charts/{name}"
    query_string = urlencode(params)
    full_url = f"{base_url}?{query_string}"

    if full_url not in logged_urls:
        logged_urls.add(full_url)
        with open(LOG_FILE, "a") as f:
            f.write(full_url + "\n")



@app.route('/charts/<name>', methods=['GET', 'POST'])
def charts(name):
    auth = True
    if request.method == 'POST':
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")
        auth = request.json.get("authorization")
        api_key = request.json.get("api_key")
    else:  # GET method
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        auth = request.args.get("authorization")
        api_key = request.args.get("api_key")
    
    token = request.headers.get('Authorization')

    method="api_key"
    if token:
        method = "token"


    if method == "api_key" and (not api_key or api_key != get_env_value("ALL_FILTERS_CHART_API_KEY")):
        return {
            "error": "Incorrect API Key"
        }, 401
    elif method == "token" and token is None and auth == False:
            abort(400, description="Please provide a token")
    
    if method == "token":
        verify_token(token)
    

    

    if not start_date or not end_date:
        return jsonify({"error": "Start date or end date is missing."}), 400

    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    # Build the workload key based on name + dates + request parameters
    params = get_request_dict(request)
    log_unique_url(name, params)
    key = _chart_key(name, start_date, end_date, params)

    # Fast path: return from cache if available
    cached_data = get_cached_item(name, start_date, end_date, params)
    if cached_data:
        return jsonify(cached_data), 200

    # Coordination: either become the owner (compute) or wait for the owner to finish
    role, ev = _acquire_or_wait_for_slot(key)

    if role != "owner":
        # Not the owner; re-check cache after waiting
        cached_after_wait = get_cached_item(name, start_date, end_date, params)
        if cached_after_wait:
            return jsonify(cached_after_wait), 200

        # If still missing and the role indicates failure/timeout upstream,
        # report a transient condition; a subsequent call can retry.
        if role == "waiter_failed_or_timeout":
            return jsonify({
                "error": "Chart is still being processed or previous attempt did not complete successfully. Please retry."
            }), 503

        # Default fallback (should rarely occur if event signaling aligns with caching)
        return jsonify({
            "error": "Chart processing completed but no cached result was found. Please retry."
        }), 503

    # At this point, this request is the owner and must compute and signal completion.
    sql = SQLConn()
    sql.connect()
    transactions = Transaction(sql)

    try:
        # Get chart data from the database
        resp = getChartData(name, transactions, start_date, end_date, params=params)

        # Set cache before signaling completion so waiters can fetch it immediately
        set_cached_item(resp, name, start_date, end_date, params)

        return jsonify(resp), 200

    except Exception as e:
        resp = {
            "error": str(e),
            "chartName": name,
            "stackTrace": traceback.format_exc()
        }
        print(f"Error while fetching chart data: {str(e)}")
        return jsonify(resp), 500

    finally:
        # Always disconnect and release the in-flight slot
        try:
            sql.disconnect()
        finally:
            # Signal completion to any waiters and clean up the in-flight map
            if ev is not None:
                ev.set()
            with _INFLIGHT_LOCK:
                current = _INFLIGHT.get(key)
                # Only remove if this owner is still the current entry
                if current and current.get("event") is ev:
                    _INFLIGHT.pop(key, None)

@app.route('/msalConfig', methods=['GET'])
def msalConfig():
    return {
        "auth": {
            "clientId": get_env_value("REACT_APP_AZURE_CLIENT_ID"),
            "authority": "https://login.microsoftonline.com/" + get_env_value("REACT_APP_AZURE_TENANT_ID"),
            "redirectUri": get_env_value("REACT_APP_FE_SERVER_BASE_URL"),
            "postLogoutRedirectUri": get_env_value("REACT_APP_FE_SERVER_BASE_URL"),
        },
        "cache": {
            "cacheLocation": "localStorage",
            "storeAuthStateInCookie": False,
        },
    }

@app.route('/chart_builder', methods=['GET', 'POST'])
def chart_builder():
    from chart_builder import final
    return final(request)




@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'message': 'Both email and password are required.'}), 400
    server_address = 'ldaps://ldap.myfnb.us:636'
    server = Server(server_address, use_ssl=True, get_info=ALL)
    domain_username = f'MYFNB\\{email}'

    try:
        conn = Connection(server, user=domain_username, password=password, authentication=NTLM, auto_bind=True)

        # Perform LDAP search to get all attributes
        conn.search(search_base='dc=myfnb,dc=us',
                    search_filter=f'(sAMAccountName={email})',
                    search_scope=SUBTREE,
                    attributes=ALL_ATTRIBUTES)

        # Extract user data from search response
        if conn.entries:
            user_data = conn.entries[0]
            user_info = {attr: user_data[attr].value for attr in user_data.entry_attributes_as_dict}

            # Decode byte objects to strings
            for key, value in user_info.items():
                if isinstance(value, bytes):
                    user_info[key] = ""
            display_name =user_info.get("displayName","Unable to parse name.")
            try:
                role = get_role(user_info)
                pass 
            except:
                return jsonify({"message":"Sorry "+display_name+" does not have access to this dashboard. Please contact the admin."})

            token = jwt.encode({'email': email, 
                                'role': role, 
                                'exp': datetime.utcnow() + timedelta(minutes=int(get_env_value("REACT_APP_SESSION_TIMEOUT_MINUTES")))}, app.config['SECRET_KEY'], algorithm='HS256')
            conn.unbind()

            return jsonify({
                'message': 'Login successful.',
                'token': token,  # Decode the token to a string
                'user': display_name,
                "role": role, 
            }), 200
        else:
            conn.unbind()
            return jsonify({'message': 'User not found in LDAP.'}), 404

    except LDAPException as error:
        return jsonify({'message': "Invalid Credentials!"}), 401

@app.route('/logout')
def logout():
    return jsonify({'message': 'Logged out successfully'})

@app.route('/clear_cache')
def clear_cache():
    # Optional query parameter: days
    days = request.args.get('days', default=None, type=int)
    if days is not None and days > 0:
        # Clear cache except for the last 'days' days
        clear_all_cache(days)
        return jsonify({'message': f'Cache cleared except for the last {days} days'})
    else:
        clear_all_cache()
        return jsonify({'message': 'Cache cleared successfully'})

def verify_token(token):
    if not token:
        return 'Token is missing'
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        return None

@app.route('/refill_database', methods=['GET'])
def refill_database():
    CSV_FOLDER = app.config['CSV_FOLDER']
    if not os.path.exists(CSV_FOLDER):
        return jsonify({"error": "CSV folder not found"}), 404
    conf_file = os.path.join(CSV_FOLDER, "ctrl.conf")
    if not os.path.exists(conf_file):
        return jsonify({"error": "Control file not found"}), 404
    os.remove(conf_file)
    return jsonify({"message": "Control file removed successfully"}), 200

@app.route('/show_logs/<filename>', methods=['GET'])
def show_logs(filename):
    logs_path = os.path.join(app.config['CSV_FOLDER'], "logs")
    if not os.path.exists(logs_path):
        return jsonify({"error": "Logs folder not found"}), 404
    log_file_path = os.path.join(logs_path, filename)
    if not os.path.exists(log_file_path):
        # return list of all log files
        log_files = [f for f in os.listdir(logs_path) if f.endswith('.html')]
        # return as html
        if not log_files:
            return jsonify({"error": "No log files found"}), 404
        log_files_html = "<ul>"
        for log_file in log_files:
            log_files_html += f"<li><a href='/show_logs/{log_file}'>{log_file}</a></li>"
        log_files_html += "</ul>"
        return render_template_string("<h1>Log Files</h1>" + log_files_html)
    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        content = log_file.read()
    return render_template_string(content)

@app.route('/uptospeed')
def uptospeed():
    from csvLoader import get_csv
    update_metrics("csv_push", f"started {datetime.now().isoformat()}")
    updates = get_csv(app.config['CSV_FOLDER'])
    update_metrics("csv_push", f"ended {datetime.now().isoformat()}")
    return updates

@app.route('/xml_pull')
def xml_pull():
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    from csvLoader import update_JMExtracts
    updates = update_JMExtracts(sql, txn)


    sql.disconnect()
    
    return updates


@app.route('/query', methods=['POST'])
def get_query():
    data = request.get_json()
    query = data.get('query')


    if not query:
        return "Query parameter missing", 400
    
    if type(query) == int or type(query) == float:
        return str(query)

    if "elect" not in query.lower():
        return query

    kind = ""
    if "CRFEDW" in query:
        kind = "CRFEDW"
    if "CAMEDW" in query:
        kind = "CAMEDW"

    sql = SQLConn(kind=kind)
    sql.connect()
    resp = ""
    try:

        txn = Transaction(sql)
        resp = txn.get_transactions_by_sql_query(query)
    except:
        sql.execute(sql)
        resp = sql.connection.commit()
    sql.disconnect()

    if isinstance(resp, (list, dict)):
        return jsonify(resp)
    else:
        return str(resp)



@app.route('/show_metrics')
def metrics_api():
    return get_metrics()

@app.route('/cache')
def show_cache():
    cache_list = cached_date_list(None,None,None)
    SORT_BY = "start"
    # List of 31 distinct colors (hex codes)
    colors = [
        "#FF6633", "#FFB399", "#FF33FF", "#FFFF99", "#00B3E6",
        "#E6B333", "#3366E6", "#999966", "#99FF99", "#B34D4D",
        "#80B300", "#809900", "#E6B3B3", "#6680B3", "#66991A",
        "#FF99E6", "#CCFF1A", "#FF1A66", "#E6331A", "#33FFCC",
        "#66994D", "#B366CC", "#4D8000", "#B33300", "#CC80CC",
        "#66664D", "#991AFF", "#E666FF", "#4DB3FF", "#1AB399",
        "#E666B3"
    ]
    ret = '''
            <table>
            <tr><th>chart_start</th><th>chart_name</th><th>chart_end</th></tr>
        '''
    for object in cache_list:
        # From start date 2025-03-01, get day, and get the equivalent colour from that list
        try:
            # Parse the start date and get the day of the month (1-31)
            day = int(object[SORT_BY].split('-')[2])
            color = colors[(day - 1) % len(colors)]
        except Exception:
            color = "#FFFFFF"

        ret += f"<tr style=\"color:{color}\"><td>{object['start']}</td><td>{object['name']}</td><td>{object['end']}</td></tr>"
    return ret+"</table>"



 
if __name__ == "__main__":
    print("--------------------------------------------------------- Testing Default SQL Connection ---------------------------------------------------------")
    sql = SQLConn()
    sql.connect()
    sql.setup()
    sql.log_tables()
    sql.disconnect()
    
    print("--------------------------------------------------------- Testing EDW SQL Connection ---------------------------------------------------------")
    sql = SQLConn(kind="CRFEDW")
    sql.connect()
    sql.log_tables()    
    sql.disconnect()

    print("--------------------------------------------------------- Testing CustomerDocumentCenter SQL Connection ---------------------------------------------------------")
    sql = SQLConn(kind="CustomerDocumentCenter")
    sql.connect()
    sql.log_tables()    
    sql.disconnect()

    print("-----------------------------------------------------------------------------------------------------------------")
    
    if str(get_env_value("REACT_APP_DEBUG")).lower() == "true":
        print("Running in Debug mode")
        clear_all_cache()
        app.run(host="0.0.0.0",port=5000, debug=True)
    else:
        print("Running in Production mode")
        serve(app, host='0.0.0.0', port=5000)
