from base64 import b64encode
from datetime import timedelta, datetime, timezone
from typing import Any
import requests
from mage_ai.data_preparation.shared.secrets import get_secret_value
from langfuse.utils import constants
BASE_URL = "https://cloud.langfuse.com/api/public"

secret_name = constants.config_mapper['secret_name']
try:
    credentials = get_secret_value(secret_name)
except AttributeError:
    # this happens when running this as a script (not in mage) on a local machine
    import dotenv
    import os
    dotenv.load_dotenv()
    credentials = os.getenv(secret_name)

def fetch_all_pages(path: str, days_back: int, params: dict[str, Any] | None = None):
    headers = {
        "Authorization": f"Basic {b64encode(credentials.encode()).decode()}",
        "Content-Type": "application/json"
    }

    start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    if params is None:
        params = {}
    params['fromTimestamp'] = start_date.strftime('%Y-%m-%dT00:00:00Z')
    params['limit'] = 100 # it does not allow a higher limit
    page = 1
    all_data = []
    while True:
        params['page'] = page
        print(f"Fetching page {page}")
        response = requests.get(f"{BASE_URL}/{path}", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            extracted_data = data['data']
            if not extracted_data:
                break
            all_data.extend(extracted_data)
            page += 1
        else:
            print(f"Error fetching page {page}: {response.status_code} {response.text}")
            response.raise_for_status()
    print(f"Total pages: {page}. Total data: {len(all_data)}")
    return all_data