import pytest
import requests_mock
import json


@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_rate_limit_retry_logic(db_session):
    """
    Ensures that our function re-attempts after a 429 response.
    We mock the first call as 429, second as 200, verifying that it eventually succeeds.
    """
    from app.services.hubspot_service import create_or_update_contact

    with requests_mock.Mocker() as m:
        # Mock token refresh
        m.post(
            "https://api.hubapi.com/oauth/v1/token",
            json={
                "access_token": "MOCK_TOKEN",
                "refresh_token": "MOCK_REFRESH",
                "expires_in": 3600,
            },
        )

        # Mock the search contact endpoint
        #    - first call => 429
        #    - second call => 200 with no results
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        m.post(
            search_url,
            [
                {"status_code": 429, "json": {"message": "Rate limit exceeded"}},
                {"status_code": 200, "json": {"results": []}},
            ],
        )

        # Mock the create contact endpoint => 200
        m.post(
            "https://api.hubapi.com/crm/v3/objects/contacts", json={"id": "CONTACT_123"}
        )

        # Call create_or_update_contact
        contact_id = create_or_update_contact(
            {
                "email": "test@example.com",
                "firstname": "Test",
                "lastname": "User",
                "phone": "1234567890",
            }
        )
        assert contact_id == "CONTACT_123"

        # Check request history: ensure the search endpoint was called twice,
        # then the creation endpoint was called once
        assert len(m.request_history) == 3
        # The first was a 429, second was 200, third was the creation
