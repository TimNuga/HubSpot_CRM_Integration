import pytest
from unittest.mock import patch, MagicMock
from app.services.oauth_service import HubspotOAuthService
from app.models import HubspotAuth
from app.utils.errors import ServiceUnavailableError
from app.extensions import db
from datetime import datetime, timedelta
import requests


@pytest.mark.usefixtures("test_app", "db_session")
class TestHubspotOAuthService:
    """
    Unit tests for HubspotOAuthService (utils/oauth_service.py).
    Uses the db_session fixture for DB rollback after each test.
    """

    @patch("app.services.oauth_service.request_with_tenacity")
    def test_refresh_token_success(self, mock_request, test_app):
        """
        Ensures refresh_token() updates DB record with new tokens on success.
        """
        with test_app.app_context():
            # Clear out existing HubspotAuth if needed
            db.session.query(HubspotAuth).delete()
            db.session.commit()

            # Insert a dummy HubspotAuth with expired token
            auth_record = HubspotAuth(
                access_token="old_access_token",
                refresh_token="old_refresh_token",
                token_expires_at=datetime.utcnow() - timedelta(seconds=1),
            )
            db.session.add(auth_record)
            db.session.commit()

            # Mock the request_with_tenacity call to simulate a successful refresh
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
            }
            mock_request.return_value = mock_resp

            service = HubspotOAuthService()
            # Call the method that triggers a refresh
            service.refresh_token()

            updated_auth = HubspotAuth.query.first()
            assert updated_auth is not None
            assert updated_auth.access_token == "new_access_token"
            assert updated_auth.refresh_token == "new_refresh_token"
            assert updated_auth.token_expires_at is not None

    @patch("app.services.oauth_service.request_with_tenacity")
    def test_refresh_token_failure(self, mock_request, test_app):
        """
        Ensures refresh_token() raises ServiceUnavailableError if the request fails.
        """
        with test_app.app_context():
            # Ensure we have a record
            db.session.query(HubspotAuth).delete()
            db.session.commit()

            auth_record = HubspotAuth(
                access_token="old_access",
                refresh_token="old_refresh",
                token_expires_at=datetime.utcnow() - timedelta(seconds=1),
            )
            db.session.add(auth_record)
            db.session.commit()

            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = requests.HTTPError("Bad Request")
            mock_request.return_value = mock_resp

            service = HubspotOAuthService()
            with pytest.raises(ServiceUnavailableError) as excinfo:
                service.refresh_token()
            assert "Unable to refresh HubSpot token." in str(excinfo.value)

    @patch("app.services.oauth_service.request_with_tenacity")
    def test_get_access_token_auto_refresh(self, mock_request, test_app):
        """
        If the token is expired, get_access_token() triggers refresh.
        """
        with test_app.app_context():
            # Insert a record with an expired token_expires_at
            db.session.query(HubspotAuth).delete()
            db.session.commit()

            expired_time = datetime.utcnow() - timedelta(seconds=1)
            auth_record = HubspotAuth(
                access_token="expired_access",
                refresh_token="refresh_me",
                token_expires_at=expired_time,
            )
            db.session.add(auth_record)
            db.session.commit()

            # Mock success
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "access_token": "new_access",
                "refresh_token": "new_ref",
                "expires_in": 1800,
            }
            mock_request.return_value = mock_resp

            service = HubspotOAuthService()
            token = service.get_access_token()
            assert token == "new_access"
