import logging
from flask import current_app
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result
)
import requests

logger = logging.getLogger(__name__)

def _is_rate_limit_or_server_error(response: requests.Response) -> bool:
    """
    Return True if the response indicates a rate-limit (429) or server error (5xx).
    We only want to retry these scenarios.
    """
    if response.status_code == 429:
        logger.warning("Got 429 from HubSpot: Rate limited.")
        return True
    if 500 <= response.status_code < 600:
        logger.warning("Got 5xx from HubSpot: transient server error.")
        return True
    return False

def _needs_retry(resp: requests.Response) -> bool:
    """
    This function is used by tenacity's `retry_if_result`.
    If it returns True, tenacity triggers a retry.
    """
    return _is_rate_limit_or_server_error(resp)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1.0, min=1, max=30),
    retry=retry_if_result(_needs_retry) | retry_if_exception_type(
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
    reraise=True
)
def request_with_tenacity(method: str, url: str, **kwargs) -> requests.Response:
    """
    A generic request function that uses Tenacity to retry on:
      - 429 (rate limit)
      - 5xx (transient server errors)
      - Connection/Timeout errors
    We'll raise_for_status() only if it's not a rate-limit or server error we plan to handle.
    """
    resp = requests.request(method, url, **kwargs)
    if _is_rate_limit_or_server_error(resp):
        # If we see a 429 or 5xx, we let Tenacity do a retry
        return resp
    # For 2xx or 4xx (not 429), raise an exception to fail fast
    # e.g., 400 or 404 or 403 won't be retried
    resp.raise_for_status()
    return resp
