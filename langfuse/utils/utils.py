import math
import os
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from typing import Any

import dotenv
import requests
from loguru import logger
from mage_ai.data_preparation.shared.secrets import get_secret_value
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from langfuse.utils import constants

BASE_URL = "https://cloud.langfuse.com/api/public"

secret_name = constants.config_mapper["secret_name"]
try:
    credentials = get_secret_value(secret_name)
except AttributeError:
    # this happens when running this as a script (not in mage) on a local machine)
    dotenv.load_dotenv()
    credentials = os.getenv(secret_name)

attempt_count = 5

def get_retry_after(response):
    """
    Extracts the 'Retry-After' header (if it exists) and returns the time in seconds as an integer.
    If there's no valid 'Retry-After' or an error occurs, returns None.
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return math.ceil(float(retry_after))
    except (ValueError, TypeError):
        return None


def wait_time(retry_state):
    """
    Returns the primary wait time, checking if status_code == 429. 
    Uses the 'Retry-After' header if available. Otherwise, defaults to 1 second.
    """
    default_wait = 5 # seconds
    if (
        hasattr(retry_state.outcome, "exception")
        and hasattr(retry_state.outcome.exception(), "response")
        and retry_state.outcome.exception().response.status_code == 429
    ):
        val = get_retry_after(retry_state.outcome.exception().response) or default_wait
    else:
        """
        Returns the fallback wait time, using exponential backoff
        if the Retry-After header isn't applicable.
        """
        val = 2 ** (retry_state.attempt_number - 1)
    return wait_fixed(val)(retry_state)



def log_before_sleep(retry_state):
    """
    Logs a warning message before sleeping in a retry attempt.
    """
    logger.warning(
        f"Request failed. Attempt {retry_state.attempt_number}/{attempt_count}. "
        f"Waiting {retry_state.next_action.sleep if retry_state.next_action else 'unknown'} seconds before retry. "
    )

@retry(
    stop=stop_after_attempt(attempt_count),
    wait=wait_time,
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    before_sleep=log_before_sleep
)
def make_request(url, headers, params):
    """
    Performs an HTTP GET request with retries. Raises an exception if all attempts fail.
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response
    except Exception:
        logger.exception(f"Request failed: {url=}, {params=}")
        raise


def fetch_all_pages(path: str, days_back: int, params: dict[str, Any] | None = None):
    """
    Fetches the data for multiple pages, up to the limit imposed by the given path,
    starting from 'days_back' days ago until now (UTC). 
    Returns a list combining all pages of data.
    """
    headers = {
        "Authorization": f"Basic {b64encode(credentials.encode()).decode()}",
        "Content-Type": "application/json"
    }

    start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    if params is None:
        params = {}
    params["fromTimestamp"] = start_date.strftime("%Y-%m-%dT00:00:00Z")
    params["limit"] = 100  # API does not allow a higher limit (tested via experimentation)

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
