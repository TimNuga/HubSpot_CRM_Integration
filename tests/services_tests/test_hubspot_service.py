import pytest
from unittest.mock import patch, MagicMock
from flask import current_app
from app.models import CreatedCRMObject, db
from app.services.oauth_service import HubspotOAuthService
from app.services.hubspot_service import HubSpotService


@pytest.mark.usefixtures("test_app", "db_session")
class TestHubSpotService:
    """
    Unit tests for HubSpotService.
    We'll mock out HubSpotAPI calls to avoid real network traffic.
    """

    @patch("app.services.hubspot_service.HubspotOAuthService")
    @patch("app.services.hubspot_service.HubSpotAPI")
    def test_upsert_contact_creates_if_not_found(
        self, mock_api_cls, mock_oauth_cls, db_session
    ):
        """
        If find_contact_by_email returns None, we create a new contact
        and store a CreatedCRMObject record.
        """
        mock_oauth = mock_oauth_cls.return_value
        mock_oauth.get_access_token.return_value = "DUMMY_TOKEN"

        mock_api = mock_api_cls.return_value
        mock_api.find_contact_by_email.return_value = None
        mock_api.create_contact.return_value = {
            "id": "CONTACT_123",
            "properties": {"email": "test@example.com"},
        }

        service = HubSpotService()  # uses the mocked classes

        contact_data = {
            "email": "test@example.com",
            "firstname": "Test",
            "lastname": "User",
            "phone": "12345",
        }
        result = service.upsert_contact(contact_data)
        assert result["id"] == "CONTACT_123"

        # Check that we stored a local CreatedCRMObject
        local_obj = (
            db_session.query(CreatedCRMObject)
            .filter_by(external_id="CONTACT_123", object_type="contacts")
            .first()
        )
        assert local_obj is not None
        assert local_obj.name == "test@example.com"

    @patch("app.services.hubspot_service.HubspotOAuthService")
    @patch("app.services.hubspot_service.HubSpotAPI")
    def test_upsert_deal_updates_if_found(
        self, mock_api_cls, mock_oauth_cls, db_session
    ):
        """
        If find_deal_by_name returns an existing record, we update it
        and store a local CreatedCRMObject reference.
        """
        mock_oauth = mock_oauth_cls.return_value
        mock_oauth.get_access_token.return_value = "DUMMY_TOKEN"

        mock_api = mock_api_cls.return_value
        mock_api.find_deal_by_name.return_value = {
            "id": "DEAL_001",
            "properties": {"dealname": "Existing Deal"},
        }
        mock_api.update_deal.return_value = {
            "id": "DEAL_001",
            "properties": {"dealname": "Updated Deal"},
        }

        service = HubSpotService()

        deal_data = {
            "dealname": "Existing Deal",
            "amount": 500,
            "dealstage": "appointmentscheduled",
        }
        result = service.upsert_deal(deal_data)
        assert result["id"] == "DEAL_001"
        assert result["properties"]["dealname"] == "Updated Deal"

        local_obj = (
            db_session.query(CreatedCRMObject)
            .filter_by(external_id="DEAL_001", object_type="deals")
            .first()
        )
        assert local_obj is not None
        assert local_obj.name == "Updated Deal"

    @patch("app.services.hubspot_service.HubspotOAuthService")
    @patch("app.services.hubspot_service.HubSpotAPI")
    def test_create_ticket_with_associations(
        self, mock_api_cls, mock_oauth_cls, db_session
    ):
        """
        Tests that create_ticket associates contact/deal if provided
        and stores a local record.
        """
        mock_oauth = mock_oauth_cls.return_value
        mock_oauth.get_access_token.return_value = "DUMMY_TOKEN"

        mock_api = mock_api_cls.return_value
        mock_api.create_ticket.return_value = {
            "id": "TICKET_ABC",
            "properties": {"subject": "Test Ticket"},
        }

        service = HubSpotService()
        ticket_data = {
            "subject": "Test Ticket",
            "description": "desc",
            "category": "technical_issue",
            "pipeline": "support_pipeline",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1",
            "contact_id": "CONTACT_123",
            "deal_id": "DEAL_456",
        }
        result = service.create_ticket(ticket_data)
        assert result["id"] == "TICKET_ABC"

        # Check local DB
        local_obj = (
            db_session.query(CreatedCRMObject)
            .filter_by(external_id="TICKET_ABC", object_type="tickets")
            .first()
        )
        assert local_obj is not None
        assert local_obj.name == "Test Ticket"

        # Check that associate calls happened
        mock_api.associate_ticket_with_contact.assert_called_once_with(
            "TICKET_ABC", "CONTACT_123"
        )
        mock_api.associate_ticket_with_deal.assert_called_once_with(
            "TICKET_ABC", "DEAL_456"
        )
