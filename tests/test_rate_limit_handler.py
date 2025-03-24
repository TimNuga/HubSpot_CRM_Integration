import pytest
from unittest.mock import patch, MagicMock
import requests
from requests import Response
from tenacity import RetryError

from app.utils.rate_limit_handler import request_with_tenacity
from app.utils.errors import RateLimitExceededError, ServiceUnavailableError


def _mock_response(status_code=200):
    """
    Helper to create a mock requests.Response with a given status_code.
    """
    resp = MagicMock(spec=Response)
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


@patch("app.utils.rate_limit_handler.requests.request")
def test_successful_request_no_retry(mock_request):
    """
    If the first call is 2xx, we do not retry, and return that response.
    """
    mock_request.return_value = _mock_response(200)
    resp = request_with_tenacity("GET", "https://example.com")
    assert resp.status_code == 200
    mock_request.assert_called_once()


@patch("app.utils.rate_limit_handler.requests.request")
def test_client_error_no_retry(mock_request):
    """
    If the call is a 4xx (not 429), we fail fast (resp.raise_for_status).
    e.g. 400, 404 => no retry
    """
    r = _mock_response(404)
    r.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mock_request.return_value = r

    with pytest.raises(requests.HTTPError) as excinfo:
        request_with_tenacity("GET", "https://example.com")

    assert "404 Not Found" in str(excinfo.value)
    mock_request.assert_called_once()  # No retry attempts


@patch("app.utils.rate_limit_handler.requests.request")
def test_429_retry_then_success(mock_request):
    """
    First attempt => 429, second => 200 => success, total 2 calls.
    """
    mock_request.side_effect = [_mock_response(429), _mock_response(200)]
    resp = request_with_tenacity("POST", "https://example.com")
    assert resp.status_code == 200
    assert mock_request.call_count == 2


@patch("app.utils.rate_limit_handler.requests.request")
def test_429_persistent_final_raises(mock_request):
    """
    If all 5 attempts return 429, final callback raises RateLimitExceededError.
    """
    r = _mock_response(429)
    mock_request.return_value = r

    with pytest.raises(RateLimitExceededError) as exc:
        request_with_tenacity("GET", "https://example.com")

    assert "Max rate limit retries exceeded (429)." in str(exc.value)
    # Called 5 times in total
    assert mock_request.call_count == 5


@patch("app.utils.rate_limit_handler.requests.request")
def test_503_retry_then_success(mock_request):
    """
    First attempt => 503, second => 200 => success.
    """
    mock_request.side_effect = [_mock_response(503), _mock_response(200)]
    resp = request_with_tenacity("GET", "https://example.com")
    assert resp.status_code == 200
    # Called twice
    assert mock_request.call_count == 2


@patch("app.utils.rate_limit_handler.requests.request")
def test_503_persistent_final_raises(mock_request):
    """
    If all attempts return 503, final callback raises ServiceUnavailableError
    (based on your code).
    """
    r = _mock_response(503)
    mock_request.return_value = r

    with pytest.raises(ServiceUnavailableError) as exc:
        request_with_tenacity("GET", "https://hubspot.com")

    assert "Service Unavailable Error (503)" in str(exc.value)
    # Attempted 5 times
    assert mock_request.call_count == 5


@patch("app.utils.rate_limit_handler.requests.request")
def test_500_persistent_final_raises_httperror(mock_request):
    """
    If all attempts return 500, final callback logs error and calls final_resp.raise_for_status()
    resulting in an HTTPError.
    """
    r = _mock_response(500)
    # We'll mimic raise_for_status raising an HTTPError
    r.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_request.return_value = r

    with pytest.raises(requests.HTTPError) as exc:
        request_with_tenacity("PATCH", "https://example.com")

    assert "500 Server Error" in str(exc.value)
    assert mock_request.call_count == 5
