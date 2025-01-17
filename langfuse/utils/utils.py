from base64 import b64encode
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from loguru import logger
from mage_ai.data_preparation.shared.secrets import get_secret_value
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from langfuse.utils import constants

BASE_URL = "https://cloud.langfuse.com/api/public"

secret_name = constants.config_mapper["secret_name"]
try:
    credentials = get_secret_value(secret_name)
except AttributeError:
    # this happens when running this as a script (not in mage) on a local machine
    import os

    import dotenv
    dotenv.load_dotenv()
    credentials = os.getenv(secret_name)


def create_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session

def make_request(url, headers, params):
    session = create_session()
    try:
        response = session.get(url, headers=headers, params=params)
        return response
    except Exception:
        logger.exception(f"Request failed: {url=}, {params=}")
    finally:
        session.close()

def fetch_all_pages(path: str, days_back: int, params: dict[str, Any] | None = None):
    headers = {
        # using headers (instead of `auth=` param) because secrets are stored together in one string pk-...:sk-...
        "Authorization": f"Basic {b64encode(credentials.encode()).decode()}",
        "Content-Type": "application/json"
    }

    start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    if params is None:
        params = {}
    params["fromTimestamp"] = start_date.strftime("%Y-%m-%dT00:00:00Z")
    params["limit"] = 100 # API does not allow a higher limit (tried via experimentation)
    page = 1
    all_data = []
    while True:
        params["page"] = page
        logger.info(f"Fetching page {page}")
        response = make_request(f"{BASE_URL}/{path}", headers, params)
        if response.status_code == 200:
            data = response.json()
            extracted_data = data["data"]
            if not extracted_data:
                break
            all_data.extend(extracted_data)
            page += 1
        else:
            logger.error(f"Error fetching page {page}: {response.status_code} {response.text}")
            response.raise_for_status()
    logger.info(f"Total pages: {page}. Total data: {len(all_data)}")
    return all_data
