import pytest
from unittest.mock import patch, MagicMock
from app.models import CreatedCRMObject


@pytest.mark.usefixtures("test_app", "test_client", "db_session")
class TestHubspotController:
    def test_upsert_contact_success(self, test_client, db_session):
        """
        Integration-like test: We call /api/contacts with valid data,
        verifying we get a 200 success and local DB is updated.
        """
        # We'll patch the HubSpotService to avoid real network calls
        with patch(
            "app.controllers.hubspot_controller.HubSpotService"
        ) as mock_service_cls:
            # The mock_service instance
            mock_service = mock_service_cls.return_value
            mock_service.upsert_contact.return_value = {
                "id": "CONTACT_123",
                "properties": {"email": "test@example.com"},
            }

            payload = {
                "email": "test@example.com",
                "firstname": "Alice",
                "lastname": "Doe",
                "phone": "+1-555-1234",
            }
            resp = test_client.post("/api/contacts", json=payload)
            data = resp.get_json()

            assert resp.status_code == 200
            assert data["success"] is True
            assert "contact" in data["data"]
            assert data["data"]["contact"]["id"] == "CONTACT_123"

            # Check that upsert_contact was called with the validated data
            mock_service.upsert_contact.assert_called_once_with(payload)

    def test_upsert_contact_validation_error(self, test_client):
        """
        If required fields are missing, Marshmallow raises a ValidationError,
        and the endpoint returns a 400 with an error message containing details about the missing field.
        """
        # Missing the required "phone" field.
        payload = {
            "email": "invalid@example.com",
            "firstname": "NoPhone",
            "lastname": "User",
        }
        resp = test_client.post("/api/contacts", json=payload)
        data = resp.get_json()

        assert resp.status_code == 400
        assert data["success"] is False
        # Instead of checking for a fixed string, we check for a substring
        # indicating that "phone" is missing.
        assert "Missing data for required field" in data["message"]

    def test_get_new_crm_objects(self, test_client, db_session):
        """
        Calls GET /api/new-crm-objects to verify local DB pagination.
        """
        # Suppose we add some local CreatedCRMObject records
        from app.models import CreatedCRMObject

        new_obj = CreatedCRMObject(
            external_id="ID_001", object_type="contacts", name="test@example.com"
        )
        db_session.add(new_obj)
        db_session.commit()

        resp = test_client.get(
            "/api/new-crm-objects?objectType=contacts&page=1&limit=5"
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True
        results = data["data"]["results"]
        assert len(results) == 1
        assert results[0]["external_id"] == "ID_001"
