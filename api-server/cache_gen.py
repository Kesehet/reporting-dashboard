import os
import json
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from metrics import update_metrics

update_metrics("cache_gen", f"started {datetime.now().isoformat()}")
# Load environment variables from .env file
load_dotenv()
BASE_URL = os.getenv("REACT_APP_API_SERVER_BASE_URL")
API_KEY= os.getenv("ALL_FILTERS_CHART_API_KEY")

# Function to resolve __OFFSET_N__ placeholders in URLs
def resolve_url_placeholders(url):
    def replace_offset(match):
        offset = int(match.group(1))
        date = datetime.today() + timedelta(days=offset)
        return date.strftime("%Y-%m-%d")
    return re.sub(r"__OFFSET_(-?\d+)__", replace_offset, url)




def strip_api_key_query(url_path):
    """Remove outdated URL credentials while preserving other encoded filters."""
    path, separator, query = url_path.partition("?")
    if not separator:
        return url_path
    filters = [part for part in query.split("&") if part.split("=", 1)[0].lower() != "api_key"]
    return path + ("?" + "&".join(filters) if filters else "")


# Read URLs from the text file, without replaying legacy URL credentials.
with open("logged_chart_urls.txt", "r") as f:
    urls = [strip_api_key_query(line.strip()) for line in f if line.strip()]
unique_urls = list(set(urls))
unique_urls.sort()

with open("logged_chart_urls.txt", "w") as f:
    for url in unique_urls:
        f.write(url+"\n")


# Prepare list to store JSON responses
responses = []

update_metrics("cache_gen_error", f"Starting to generate cache for {len(urls)}.")


ctr = 0
# Ping each URL and collect the response
for url_path in urls:
    ctr += 1
    resolved_path = resolve_url_placeholders(url_path)
    full_url = BASE_URL.rstrip("/") + resolved_path
    try:
        response = requests.get(full_url, headers={'X-API-KEY': API_KEY}, timeout=60)
        response.raise_for_status()
        update_metrics("cache_gen_error", f"Generated cache for {ctr}/{len(urls)}.")
    except Exception as e:
        update_metrics("cache_gen_error", str(e))



print(f"Completed requests to {len(urls)} URLs.")
update_metrics("cache_gen", f"ended {datetime.now().isoformat()}")
update_metrics("cache_gen_error", f"No Error. Cached {len(urls)} URLs. ")



