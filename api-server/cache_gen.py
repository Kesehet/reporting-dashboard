import os
import json
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from metrics import update_metrics





update_metrics("csv_gen", f"started {datetime.now().isoformat()}")
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

# Read URLs from the text file
with open("logged_chart_urls.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

# Prepare list to store JSON responses
responses = []

# Ping each URL and collect the response
for url_path in urls:
    resolved_path = resolve_url_placeholders(url_path)
    full_url = BASE_URL.rstrip("/") + resolved_path
    if "?" in full_url:
        full_url = full_url + "&api_key="+API_KEY
    else:
        full_url = full_url + "?api_key="+API_KEY
    print("Pinged "+ full_url)
    try:
        response = requests.get(full_url)
        response.raise_for_status()
        responses.append(response.json())
        print(f"    - {response.status_code}")
    except Exception as e:
        responses.append({"error": str(e), "url": full_url})

# Save all responses to a JSON file
with open("chart_responses.json", "w") as f:
    json.dump(responses, f, indent=2)

print(f"Completed requests to {len(urls)} URLs. Responses saved to chart_responses.json.")
update_metrics("csv_gen", f"ended {datetime.now().isoformat()}")