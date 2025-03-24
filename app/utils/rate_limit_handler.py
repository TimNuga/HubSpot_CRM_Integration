import logging
import requests
from requests import Response

from flask import current_app
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    RetryCallState,
)
from .errors import RateLimitExceededError, ServiceUnavailableError

logger = logging.getLogger(__name__)


def _is_rate_limit_or_server_error(response: Response) -> bool:
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


def _needs_retry(resp: Response) -> bool:
    """
    This function is used by tenacity's `retry_if_result`.
    If it returns True, tenacity triggers a retry.
    """
    return _is_rate_limit_or_server_error(resp)


def _final_attempt_callback(retry_state: RetryCallState):
    """
    Called if the final call still returns a retryable result (429/5xx).
    We raise a RateLimitExceededError if it's 429,
    or you can decide how to handle final 5xx as well.
    """
    outcome = retry_state.outcome
    if outcome and not outcome.failed:
        # Means we have a "successful" return, but it might still be a 429 or 5xx
        final_resp = outcome.result()
        status_code = final_resp.status_code
        if status_code == 429:
            # Raise your custom RateLimitExceededError
            logger.error(
                "Still got 429 after final retry. Raising RateLimitExceededError..."
            )
            raise RateLimitExceededError(
                message="Max rate limit retries exceeded (429).",
                verboseMessage="HubSpot kept returning 429 after final attempt.",
            )
        elif 500 <= status_code < 600:
            logger.error(
                "Still got %d after final retry. Raising HTTPError...",
                final_resp.status_code,
            )
            if status_code == 503:
                raise ServiceUnavailableError(
                    message="Service Unavailable Error (503)",
                    verboseMessage="Hubspot kept returning 503 after final attempt, indicating that the error is unavailable.",
                )
            final_resp.raise_for_status()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1.0, min=1, max=30),
    retry=retry_if_result(_needs_retry)
    | retry_if_exception_type(
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
    reraise=True,
    retry_error_callback=_final_attempt_callback,
)
def request_with_tenacity(method: str, url: str, **kwargs) -> requests.Response:
    """
    A single request function that uses Tenacity to retry on:
      - 429 (rate limit)
      - 5xx (transient server errors)
      - Connection/Timeout errors
    We'll raise_for_status() only if it's not a rate-limit or server error we plan to handle.
    """
    resp = requests.request(method, url, **kwargs)
    if not _is_rate_limit_or_server_error(resp):
        # For 2xx or 4xx (not 429), raise an exception to fail fast
        # e.g., 400 or 404 or 403 won't be retried
        resp.raise_for_status()
    # If we see a 429 or 5xx, we let Tenacity do a retry via _needs_retry
    return resp
