from flask import Flask, json, request, jsonify, abort, render_template_string
from flask_cors import CORS
from authentication import authentication, request_identity, unauthorized
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configuration must load before encrypted-data imports.
if getattr(sys, "frozen", False):
    load_dotenv(Path(sys.executable).resolve().parent / ".env", override=False)
load_dotenv(Path.cwd() / ".env", override=False)

from decrypt_tools import decrypt_tools
from helper.crypto_rotation import crypto_api
from datetime import datetime
import os
from DB import SQLConn, Transaction
from waitress import serve
import sched
import time
from charts import getChartData, get_request_dict
import traceback
from cache_manager import get_cached_item, set_cached_item, clear_all_cache,  cached_date_list
from config import get_env_value
from metrics import update_metrics, get_metrics
from helper.chat_serve import _INFLIGHT_LOCK, _INFLIGHT, _chart_key, _acquire_or_wait_for_slot
from urllib.parse import urlencode
from utils import insight_report_to_csv_response, format_numbers_recursive
from csvLoader import list_csv_report_files, get_tracking_codes_from_file
from csvLoader import get_tracking_code_missing_reason
# helpers for quick_insert
import tempfile
import csv
import uuid
import shutil
import json as _pyjson
# from report_modules import mob_cor_report
# exit()

scheduler = sched.scheduler(time.time, time.sleep)

app = Flask(__name__)
CORS(app)
app.register_blueprint(decrypt_tools)
app.register_blueprint(crypto_api)
app.register_blueprint(authentication)
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
                if not params[key].endswith("01"):
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




@app.route('/', methods=['GET', 'POST'])
def all_transactions():
    identity = request_identity()
    if identity is None:
        return unauthorized()
    args = (request.get_json(silent=True) or {}) if request.method == 'POST' else request.args
    start_date = args.get('start_date')
    end_date = args.get('end_date')
    if not start_date or not end_date:
        return jsonify({"error": "Both dates are required."}), 400
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format."}), 400
    sql = SQLConn()
    sql.connect()
    try:
        values = Transaction(sql).get_transactions_by_date_range(start, end)
        if isinstance(values, str):
            values = _pyjson.loads(values)
        role = identity.get('role')
        from role_filter import all_groups, role_filter
        if role in all_groups:
            values = role_filter(_pyjson.dumps(values), role)
        return jsonify(values)
    finally:
        sql.disconnect()


def _chart_http_response(payload, csv_requested=False):
    if csv_requested:
        return app.response_class(
            payload,
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="report.csv"'},
        ), 200
    return jsonify(payload), 200


@app.route('/charts/<name>', methods=['GET', 'POST'])
def charts(name):
    if request_identity() is None:
        return unauthorized()
    if request.method == 'POST':
        start_date = request.json.get("start_date")
        end_date = request.json.get("end_date")
    else:  # GET method
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")


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
    return_format = params.get("return_format", "json")
    if return_format not in ("json", "csv"):
        return jsonify({"error": "Unsupported return_format. Use json or csv."}), 400
    csv_requested = return_format == "csv" and "Insight" in name

    log_unique_url(name, params)
    key = _chart_key(name, start_date, end_date, params)

    # Fast path: return from cache if available
    cached_data = get_cached_item(name, start_date, end_date, params)
    if cached_data is not None:
        return _chart_http_response(cached_data, csv_requested)

    # Coordination: either become the owner (compute) or wait for the owner to finish
    role, ev = _acquire_or_wait_for_slot(key)

    if role != "owner":
        # Not the owner; re-check cache after waiting
        cached_after_wait = get_cached_item(name, start_date, end_date, params)
        if cached_after_wait is not None:
            return _chart_http_response(cached_after_wait, csv_requested)

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
        if csv_requested:
            # Export raw values: showComma display formatting corrupts numeric CSV.
            try:
                resp = insight_report_to_csv_response(params, resp, transactions)
            except (TypeError, ValueError) as exc:
                return jsonify({"error": str(exc), "chartName": name}), 400
        elif params.get("showComma", "true").lower() == "true":
            resp = format_numbers_recursive(resp)

        # Cache the converted representation, then use the same content type
        # for fresh responses, cache hits, and concurrent waiters.
        set_cached_item(resp, name, start_date, end_date, params)

        return _chart_http_response(resp, csv_requested)

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

@app.route('/chart_builder', methods=['GET', 'POST'])
def chart_builder():
    from chart_builder import final
    return final(request)



@app.route('/webhook/atomic/non_eca_dds_data', methods=['POST'])
def non_eca_dds_data_webhook():
    # We temporarily write it to a file.
    data = request.get_json()
    ce_id = data.get("ce_id", "unknown_ceid")
    if not ce_id:
        ce_id = "unknown_ceid"
        # return jsonify({"error": "ce_id is missing in the payload"}), 400
    # Ensure the folder exists
    os.makedirs('Atomic-Webhook/Non-ECAs', exist_ok=True)
    with open(f'Atomic-Webhook/Non-ECAs/non_eca_dds_data_{ce_id}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json', 'w') as f:
        json.dump(data, f)
    return jsonify({"message": "Data received successfully"}), 200



@app.route('/generate_cache')
def generate_cache():
    import cache_gen
    try:
        cache_gen.generate_cache(app.config['CSV_FOLDER'])
        return jsonify({'message': 'Cache generated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
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
    try:
        from csvLoader import get_csv
        update_metrics("csv_push", f"started {datetime.now().isoformat()}")
        updates = get_csv(app.config['CSV_FOLDER'])
        update_metrics("csv_push", f"ended {datetime.now().isoformat()}")
        return updates
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/quick_insert', methods=['POST', 'GET'])
def quick_insert():
    """Create temporary CSV with fake rows, process via csvLoader core path
    (skips xml pulls and post-processing), verify DB inserts, optionally clear
    inserted rows, save a JSON result and return it.

    Params (query or JSON body): count, clear_db (true/false), save_result (true/false), prefix
    """
    temp_dir = None
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
        else:
            data = request.args or {}

        count = int(data.get('count', 1))
        clear_db = str(data.get('clear_db', 'true')).lower() in ('1', 'true', 'yes')
        save_result = str(data.get('save_result', 'true')).lower() in ('1', 'true', 'yes')
        prefix = str(data.get('prefix', 'T-'))

        temp_dir = tempfile.mkdtemp(prefix='quick_insert_')
        csv_path = os.path.join(temp_dir, f'quick_insert_{int(time.time())}.csv')

        headers = [
            "eCA Tracking Code",
            "eCA ID",
            "Primary Name",
            "App Start Date",
            "App Update Date",
            "App Status",
            "Product Account Number",
            "DataSource",
        ]

        tracking_codes = []
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for i in range(count):
                code = f"{prefix}{uuid.uuid4().hex[:8]}"
                tracking_codes.append(code)
                writer.writerow({
                    "eCA Tracking Code": code,
                    "eCA ID": f"quick_{code}",
                    "Primary Name": f"Quick Tester {code}",
                    "App Start Date": now,
                    "App Update Date": now,
                    "App Status": "Submitted",
                    "Product Account Number": "00000000",
                    "DataSource": "quick_insert",
                })

        # process via csvLoader
        from csvLoader import prepare_rows, core_process

        sql = SQLConn()
        sql.connect()
        if not sql.connection:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'error': 'Failed to connect to database'}), 500

        txn = Transaction(sql)
        rows = prepare_rows(csv_path)
        insert_output = ""
        if rows:
            insert_output += core_process(rows, sql, txn)

        results = {}
        for code in tracking_codes:
            found = txn.get_transactions_by_column('eCATrackingCode', code)
            results[code] = {'found': bool(found), 'record': found if found else None}

        cleared = False
        if clear_db:
            try:
                safe_codes = ",".join(
                    "'" + str(c).replace("'", "''") + "'" for c in tracking_codes if c is not None
                )
                delete_query = f"DELETE FROM Transactions WHERE eCATrackingCode IN ({safe_codes})"
                sql.execute(delete_query)
                cleared = True
            except Exception:
                cleared = False

        sql.disconnect()

        test_result = {
            'temp_dir': temp_dir,
            'csv_file': csv_path,
            'insert_output': insert_output,
            'results': results,
            'cleared': cleared,
            'timestamp': datetime.now().isoformat(),
        }

        if save_result:
            try:
                out_file = os.path.join(temp_dir, f'quick_insert_result_{int(time.time())}.json')
                with open(out_file, 'w', encoding='utf-8') as f:
                    _pyjson.dump(test_result, f, default=str, indent=2)
                test_result['result_file'] = out_file
            except Exception:
                pass

        return jsonify(test_result), 200

    except Exception as e:
        try:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        return jsonify({'error': str(e), 'stack': traceback.format_exc()}), 500


@app.route('/csv_report_status', methods=['GET'])
def csv_report_status():
    folder_path = app.config['CSV_FOLDER']
    processed_files = set()
    ctrl_path = os.path.join(folder_path, 'ctrl.conf')
    if os.path.exists(ctrl_path):
        with open(ctrl_path, 'r', encoding='utf-8', errors='replace') as ctrl_file:
            processed_files = {line.strip() for line in ctrl_file if line.strip()}

    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date_filter', 'all')
    files = list_csv_report_files(folder_path, processed_files, status_filter=status_filter, date_filter=date_filter)
    return jsonify({
        'folder': folder_path,
        'count': len(files),
        'processed_count': sum(1 for item in files if item['processed']),
        'files': files,
    }), 200


@app.route('/csv_report_tracking_status', methods=['POST'])
def csv_report_tracking_status():
    data = request.get_json(silent=True) or {}
    file_name = data.get('file_name') or data.get('name')
    if not file_name:
        return jsonify({'error': 'A file name is required.'}), 400

    folder_path = app.config['CSV_FOLDER']
    tracking_codes = get_tracking_codes_from_file(file_name, folder_path)
    sql = SQLConn()
    sql.connect()
    txn = Transaction(sql)
    try:
        results = []
        for tracking_code in tracking_codes:
            present_in_db = txn.tracking_code_exists(tracking_code)
            missing_reason = '' if present_in_db else get_tracking_code_missing_reason(file_name, tracking_code, folder_path)
            results.append({
                'tracking_code': tracking_code,
                'present_in_db': present_in_db,
                'status': 'present' if present_in_db else 'missing',
                'reason': missing_reason,
            })

        return jsonify({
            'file_name': file_name,
            'row_count': len(tracking_codes),
            'present_count': sum(1 for item in results if item['present_in_db']),
            'missing_count': sum(1 for item in results if not item['present_in_db']),
            'tracking_codes': results,
        }), 200
    except Exception as exc:
        return jsonify({'error': str(exc), 'stack': traceback.format_exc()}), 500
    finally:
        sql.disconnect()


@app.route('/csv_report_load_file', methods=['POST'])
def csv_report_load_file():
    data = request.get_json(silent=True) or {}
    file_name = data.get('file_name') or data.get('name')
    if not file_name:
        return jsonify({'error': 'A file name is required.'}), 400

    from csvLoader import load_single_csv_file
    result = load_single_csv_file(file_name, app.config['CSV_FOLDER'])
    if result.get('success'):
        return jsonify(result), 200
    return jsonify(result), 400


@app.route('/xml_pull')
def xml_pull():
    sql = SQLConn()
    sql.connect()
    if not sql.connection:
        return jsonify({"error": "Database connection unavailable for JM extraction"}), 503
    try:
        from csvLoader import update_JMExtracts
        updates = update_JMExtracts(sql, Transaction(sql))
        return jsonify(updates), 200
    except Exception as exc:
        print(f"Journey Manager extraction failed: {type(exc).__name__}: {exc}")
        return jsonify({"error": "Journey Manager extraction failed"}), 500
    finally:
        sql.disconnect()


@app.route('/query', methods=['POST'])
def get_query():
    data = request.get_json()
    query = data.get('query')
    showComma = data.get('showComma', True)


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
    if showComma:
        resp = format_numbers_recursive(resp)

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
    #sql.setup()
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

    # Reset Cache Gen URLS
    f2 = open("base_logged_chart_urls.txt", "r")
    with open(LOG_FILE, 'w') as f:        
        f.write(f2.read())
    f2.close()

    
    if str(get_env_value("REACT_APP_DEBUG")).lower() == "true":
        print("Running in Debug mode")
        clear_all_cache()
        app.run(host="0.0.0.0",port=5000, debug=True)
    else:
        print("Running in Production mode")
        clear_all_cache()
        serve(app, host='0.0.0.0', port=5000, threads=16, connection_limit= 300, backlog=1024, channel_timeout=150)
