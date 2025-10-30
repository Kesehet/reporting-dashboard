import hashlib
import os
import pickle
from datetime import timedelta, datetime
from charts import getChartData, get_request_dict
from report_modules.condition_utils import LIST_OF_CHARTS
from DB import SQLConn, Transaction
import json

CACHE_DIR = ".cache_requests"
CACHE_EXPIRES_IN_HOURS = 24

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_cache_key(*args):
    """Generate a cache key based on the provided arguments."""
    key = "-".join(map(str, args))
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def get_cache_file_path(cache_key):
    """Get the file path for a given cache key."""
    return os.path.join(CACHE_DIR, f"{cache_key}.cache")

def is_cache_expired(timestamp):
    """Check if the cache is older than CACHE_EXPIRES_IN_HOURS hours."""
    if CACHE_EXPIRES_IN_HOURS == 0:
        return False
    return datetime.now() - timestamp > timedelta(hours=CACHE_EXPIRES_IN_HOURS)

def get_cached_item(*args):
    """
    Retrieve a cached item if available and not expired.
    If the cache is not available or expired, return None.
    """
    # Generate a unique cache key for this request
    cache_key = generate_cache_key(*args)
    cache_file = get_cache_file_path(cache_key)

    # Check if the cache file existsoutlook:\\ReddyS@fnb-corp.com\Junk%20Email
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cached_data, timestamp = pickle.load(f)
        if not is_cache_expired(timestamp):
            # Cache is valid, return the cached data
            return cached_data
        else:
            # Cache is expired, remove the file
            os.remove(cache_file)

    return None

def set_cached_item(data, *args):
    """
    Store an item in the cache with the current timestamp.
    """
    # Generate a unique cache key for this request
    cache_key = generate_cache_key(*args)
    cache_file = get_cache_file_path(cache_key)

    # Store the data and the current timestamp in the cache
    with open(cache_file, 'wb') as f:
        pickle.dump((data, datetime.now()), f)
    
# Currently not using this function
def clear_expired_cache():
    """
    Clear expired cache files.
    """
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                _, timestamp = pickle.load(f)
            if is_cache_expired(timestamp):
                print(f"Removing expired cache file: {filename}")
                os.remove(file_path)
def clear_all_cache(n=None):
    """
    Clear all cache files.
    If n is provided, only remove cache files newer than n days (based on file modification time).
    """
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            if n is not None:
                mtime = os.path.getmtime(file_path)
                file_age_days = (datetime.now() - datetime.fromtimestamp(mtime)).days
                print(f"File {filename} is {file_age_days} days old. Where n={n}")
                if file_age_days < n:
                    continue
            print(f"Removing cache file: {filename}")
            os.remove(file_path)

def get_cached_chart_data():
    sql = SQLConn()
    sql.connect()
    transactions = Transaction(sql)
    day_range = (datetime.now().date() - datetime(2023, 12, 1).date()).days + 1
    
    application_types = ["All", "Online", "Banker Assisted"]

    print(f"Caching data for last {day_range} days.")
    for x in range(day_range):
        for y in range(day_range):
            
           
            for application_type in application_types:
                if x == y:
                    continue
                # Ensure end_date is always greater than start_date
                if y >= x:
                    continue
                # # 15 days gap incase an application gets updated 
                # if x < 15 and x != 1:
                #     continue
                start_date = datetime.now() - timedelta(days=x)
                end_date = datetime.now() - timedelta(days=y)
                start_date = start_date.strftime('%Y-%m-%d')
                end_date = end_date.strftime('%Y-%m-%d')
                branches = getChartData("All Branch Ids", transactions,start_date, end_date, params={})
                if branches == 0:
                    continue
                for branch in branches.get('rows',[]):
                    if branch is None:
                        continue
                    print(f"Processing branch: {branch}")
                    exit(0)
                    print(f"Processing between {start_date} - {end_date}")
                    for name in LIST_OF_CHARTS:
                        item = get_cached_item(name, start_date, end_date)
                        cached_date_list(f"{name} | {branch} | applicaiton type {application_type}" ,start_date,end_date)
                        if item is not None:
                            continue
                        try:
                            data = getChartData(name, transactions, start_date, end_date, params={
                                "application_type": application_type,
                                "BranchID": branch,
                            })
                        except Exception as e:
                            print(e)
                            continue
                        if data is not None:
                            set_cached_item(data, name, start_date, end_date)


def cached_date_list(name, start, end):
    file_path = os.path.join(CACHE_DIR, "cached_charts.json")
    SORT_BY = "start"

    # If all arguments are None, just return the list
    if name is None and start is None and end is None:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    return []
        else:
            return []

    # Trim whitespace from name, start, and end
    name = name.strip() if isinstance(name, str) else name
    start = start.strip() if isinstance(start, str) else start
    end = end.strip() if isinstance(end, str) else end
    cache_entry = {"name": name, "start": start, "end": end}

    # Load existing cache list if it exists
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                cache_list = json.load(f)
            except Exception:
                cache_list = []
    else:
        cache_list = []

    # Check if the entry already exists
    exists = any(
        entry.get("name", "").strip() == name and
        entry.get("start", "").strip() == start and
        entry.get("end", "").strip() == end
        for entry in cache_list
    )

    if not exists:
        cache_list.append(cache_entry)
        cache_list.sort(key=lambda x: x.get("name", ""))
        # Sort by 'start' date (ascending)
        cache_list.sort(key=lambda x: x.get(SORT_BY, ""))
        with open(file_path, "w") as f:
            json.dump(cache_list, f)

    return cache_list


clear_all_cache()