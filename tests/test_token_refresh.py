# tests/test_token_refresh.py

import pytest
import time
import requests_mock


@pytest.mark.usefixtures("test_app")
def test_proactive_token_refresh(test_app):
    """
    1) Token is near expiry => we expect a refresh call to happen.
    2) Reuse the new token afterwards.
    """
    with test_app.app_context():
        # Set current token to near expiry
        now = int(time.time())
        test_app.config["HUBSPOT_ACCESS_TOKEN"] = "OLD_TOKEN"
        test_app.config["HUBSPOT_TOKEN_EXPIRES_AT"] = now + 10  # expires in 10s
        test_app.config["TOKEN_REFRESH_BUFFER"] = (
            30  # We'll refresh if less than 30s left
        )

        from app.hubspot_service import get_or_refresh_access_token

        with requests_mock.Mocker() as m:
            # We'll mock the refresh endpoint
            m.post(
                "https://api.hubapi.com/oauth/v1/token",
                json={
                    "access_token": "NEW_TOKEN",
                    "refresh_token": "NEW_REFRESH",
                    "expires_in": 3600,
                },
            )

            token = get_or_refresh_access_token()
            assert token == "NEW_TOKEN"
            # Verify the config updated
            assert test_app.config["HUBSPOT_ACCESS_TOKEN"] == "NEW_TOKEN"
            assert test_app.config["HUBSPOT_REFRESH_TOKEN"] == "NEW_REFRESH"
            assert test_app.config["HUBSPOT_TOKEN_EXPIRES_AT"] > now

            # Ensure the request was made
            history = m.request_history
            assert len(history) == 1
            assert history[0].url == "https://api.hubapi.com/oauth/v1/token"


@pytest.mark.usefixtures("test_app")
def test_no_refresh_if_plenty_of_time(test_app):
    """
    If the current token has plenty of time left,
    we do NOT call the refresh endpoint.
    """
    with test_app.app_context():
        now = int(time.time())
        test_app.config["HUBSPOT_ACCESS_TOKEN"] = "VALID_TOKEN"
        test_app.config["HUBSPOT_TOKEN_EXPIRES_AT"] = now + 300  # 5 min
        test_app.config["TOKEN_REFRESH_BUFFER"] = 60

        from app.hubspot_service import get_or_refresh_access_token

        with requests_mock.Mocker() as m:
            # No POST to /oauth/v1/token should occur
            token = get_or_refresh_access_token()
            assert token == "VALID_TOKEN"
            # Confirm no calls to token endpoint
            assert len(m.request_history) == 0
