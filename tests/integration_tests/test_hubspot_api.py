import pytest
from unittest.mock import patch, MagicMock
from flask import current_app
import requests
from app.integrations.hubspot_api import HubSpotAPI


class TestHubSpotAPI:
    """
    Unit tests for app.integrations.hubspot_api, verifying that we:
      - call request_with_tenacity with correct parameters
      - handle responses correctly
      - raise if request fails
    """

    @patch("app.integrations.hubspot_api.request_with_tenacity")
    def test_find_contact_by_email_found(self, mock_request):
        """
        If HubSpot returns a matching contact, we parse the 'results' array
        and return the first result.
        """
        # Setup mock to return a response with data
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "total": 1,
            "results": [
                {"id": "CONTACT_123", "properties": {"email": "found@example.com"}}
            ],
        }
        mock_request.return_value = mock_resp

        api = HubSpotAPI(token="DUMMY_TOKEN")
        contact = api.find_contact_by_email("found@example.com")

        # Verify the call to request_with_tenacity
        mock_request.assert_called_once_with(
            "POST",
            f"{api.base_url}/crm/v3/objects/contacts/search",
            headers={
                "Authorization": "Bearer DUMMY_TOKEN",
                "Content-Type": "application/json",
            },
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": "found@example.com",
                            }
                        ]
                    }
                ],
                "properties": ["email", "firstname", "lastname", "phone"],
            },
            timeout=20,
        )
        assert contact["id"] == "CONTACT_123"

    @patch("app.integrations.hubspot_api.request_with_tenacity")
    def test_find_contact_by_email_none(self, mock_request):
        """
        If HubSpot returns total=0, we return None.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"total": 0, "results": []}
        mock_request.return_value = mock_resp

        api = HubSpotAPI(token="DUMMY_TOKEN")
        contact = api.find_contact_by_email("notfound@example.com")
        assert contact is None

    @patch("app.integrations.hubspot_api.request_with_tenacity")
    def test_create_contact_raises_on_error(self, mock_request):
        """
        If request raises an exception, ensure we log error and re-raise.
        """
        # Simulate a RequestException
        mock_request.side_effect = requests.exceptions.RequestException("Network fail")

        api = HubSpotAPI("DUMMY_TOKEN")
        with pytest.raises(requests.exceptions.RequestException):
            api.create_contact({"email": "fail@example.com"})

    @patch("app.integrations.hubspot_api.request_with_tenacity")
    def test_create_contact_success(self, mock_request):
        """
        If create_contact returns a 2xx, we parse and return resp.json().
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "CONTACT_234"}
        mock_request.return_value = mock_resp

        api = HubSpotAPI("FAKE_TOKEN")
        resp_data = api.create_contact({"email": "ok@example.com"})
        assert resp_data["id"] == "CONTACT_234"
        mock_request.assert_called_once_with(
            "POST",
            f"{api.base_url}/crm/v3/objects/contacts",
            headers={
                "Authorization": "Bearer FAKE_TOKEN",
                "Content-Type": "application/json",
            },
            json={"properties": {"email": "ok@example.com"}},
            timeout=20,
        )
