import math
import os
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import dotenv
import requests
from mage_ai.data_preparation.shared.secrets import get_secret_value
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from lodgify.utils.ai_assistant import constants
from lodgify.utils.ai_assistant.logger import logger

BASE_URL = "https://cloud.langfuse.com/api/public"

secret_name = constants.get_config_mapper()["secret_name"]
try:
    credentials = get_secret_value(secret_name)
except AttributeError:
    # this happens when running this as a script (not in mage) on a local machine)
    dotenv.load_dotenv()
    credentials = os.getenv(secret_name)
    assert credentials is not None, f"Credentials for {secret_name} not found"

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
    default_wait = 5  # seconds
    if (
        hasattr(retry_state.outcome, "exception")
        and hasattr(retry_state.outcome.exception(), "response")
        and retry_state.outcome.exception().response is not None
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
    before_sleep=log_before_sleep,
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
        logger.warning(f"Request failed: {url=}, {params=}")
        raise


def calculate_start_and_end_dates(days_back: int, **kwargs) -> tuple[str, str]:
    # backfill-ready format: https://www.youtube.com/watch?v=V-wUccaafEo&ab_channel=Mage
    now_date = kwargs.get("execution_date")
    if now_date is not None:
        # Just get the date component without timezone conversion
        logger.info(f"Using initial {now_date=}")
        now_date = now_date.date()
        logger.info(f"After conversion {now_date=}")
    else:
        logger.warning("Execution date is not set, using current date (local environment)")
        now_date = datetime.now(datetime.now().astimezone().tzinfo).date()

    # not using timezone UTC here because we want to use machine local time first
    start_from_date = now_date - timedelta(days=days_back)
    # now, that we have calcualted based on the local timezone
    # we specify the date in UTC for langfuse
    start_from_date_str = start_from_date.strftime("%Y-%m-%dT00:00:00Z")
    end_date_str = now_date.strftime("%Y-%m-%dT00:00:00Z")
    return start_from_date_str, end_date_str


def fetch_all_pages(
    path: Literal["traces", "observations", "scores"],
    start_from_date: str,
    end_date: str,
    params: dict[str, Any] | None = None,
):
    """
    Fetches the data for multiple pages, up to the limit imposed by the given path,
    starting from 'start_from_date' until 'end_date' (UTC).
    Returns a list combining all pages of data.
    """
    if params is None:
        params = {}
    match path:
        case "traces" | "scores":
            # explanation of parameters from https://api.reference.langfuse.com/#get-/api/public/traces
            # traces: Optional filter to only include traces with a trace.timestamp on or after a certain datetime (ISO 8601)
            # # explanation of parameters from https://api.reference.langfuse.com/#get-/api/public/scores
            # scores: Optional filter to only include scores created on or after a certain datetime (ISO 8601)
            params["fromTimestamp"] = start_from_date
            params["toTimestamp"] = end_date
        case "observations":
            # explanation of parameters from https://api.reference.langfuse.com/#get-/api/public/observations
            # Retrieve only observations with a start_time or or after this datetime (ISO 8601).
            params["fromStartTime"] = start_from_date
            params["toStartTime"] = end_date
    params["limit"] = 100  # API does not allow a higher limit (tested via experimentation)

    headers = {"Authorization": f"Basic {b64encode(credentials.encode()).decode()}", "Content-Type": "application/json"}
    page = 1
    all_data = []
    while True:
        params["page"] = page
        if page % 10 == 0:
            logger.debug(f"Fetching page {page}")
        response = make_request(f"{BASE_URL}/{path}", headers, params)

        if response.status_code != 200:
            logger.error(f"Error fetching page {page}: {response.status_code} {response.text}")
            response.raise_for_status()

        data = response.json()
        extracted_data = data["data"]
        if not extracted_data:
            break
        all_data.extend(extracted_data)
        page += 1

    return all_data
