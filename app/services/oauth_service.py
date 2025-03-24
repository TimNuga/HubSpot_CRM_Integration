import datetime
import requests
from flask import current_app
from requests.exceptions import RequestException
from app.utils.rate_limit_handler import request_with_tenacity

from app.models import HubspotAuth, db
from app.utils.errors import ServiceUnavailableError


class HubspotOAuthService:
    """
    Manages the HubSpot token refresh lifecycle.
    """

    def __init__(self):
        # Ensure we have at least one record in the DB
        self._auth_record = HubspotAuth.query.first()
        if not self._auth_record:
            self._auth_record = HubspotAuth(
                access_token="",
                refresh_token=current_app.config["HUBSPOT_REFRESH_TOKEN"],
                token_expires_at=datetime.datetime.utcnow(),
            )
            db.session.add(self._auth_record)
            db.session.commit()

    def get_access_token(self) -> str:
        """
        Returns a valid access token, refreshing if necessary.
        """
        now = datetime.datetime.utcnow()
        if now >= self._auth_record.token_expires_at:
            current_app.logger.info("Token expired; refreshing HubSpot token.")
            self.refresh_token()

        return self._auth_record.access_token

    def refresh_token(self):
        """
        Refresh the HubSpot access token using the stored refresh token.
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": current_app.config["HUBSPOT_CLIENT_ID"],
            "client_secret": current_app.config["HUBSPOT_CLIENT_SECRET"],
            "refresh_token": self._auth_record.refresh_token,
        }
        try:
            resp = request_with_tenacity(
                "POST",
                current_app.config["HUBSPOT_OAUTH_TOKEN_URL"],
                data=data,
                timeout=10,
            )
            resp.raise_for_status()

            tokens = resp.json()
            self._auth_record.access_token = tokens["access_token"]
            self._auth_record.refresh_token = tokens.get(
                "refresh_token", self._auth_record.refresh_token
            )

            expires_in = tokens.get("expires_in", 3600)
            self._auth_record.token_expires_at = (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in - 60)
            )
            db.session.commit()

            current_app.logger.info("HubSpot token refreshed successfully.")
        except RequestException as e:
            current_app.logger.error("Failed to refresh token: %s", str(e))
            raise ServiceUnavailableError(
                message="Unable to refresh HubSpot token.", verboseMessage=str(e)
            )
