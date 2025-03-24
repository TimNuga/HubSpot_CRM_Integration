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

    @patch("app.services.hubspot_service.HubSpotService.upsert_deal")
    def test_upsert_deals_calls_upsert_deal(self, mock_upsert_deal, db_session):
        """
        Ensures upsert_deals() calls upsert_deal() for each deal in the list
        and returns the aggregated results.
        """
        service = HubSpotService()
        deals_data = [
            {
                "dealname": "Bulk Deal 1",
                "amount": 50,
                "dealstage": "appointmentscheduled",
            },
            {"dealname": "Bulk Deal 2", "amount": 150, "dealstage": "qualifiedtobuy"},
        ]
        # Mock each single upsert_deal call to return a distinct "result"
        mock_upsert_deal.side_effect = [
            {"id": "DEAL_111", "properties": {"dealname": "Bulk Deal 1"}},
            {"id": "DEAL_222", "properties": {"dealname": "Bulk Deal 2"}},
        ]

        results = service.upsert_deals(deals_data)

        assert len(results) == 2
        assert results[0]["id"] == "DEAL_111"
        assert results[1]["id"] == "DEAL_222"
        # Verify that upsert_deal was called twice
        assert mock_upsert_deal.call_count == 2

    @patch("app.services.hubspot_service.HubSpotService.create_ticket")
    def test_create_tickets_calls_create_ticket(self, mock_create_ticket):
        """
        Ensures create_tickets() calls create_ticket() for each ticket in the list
        and returns the aggregated results.
        """
        service = HubSpotService()
        tickets_data = [
            {
                "subject": "Bulk Tix A",
                "description": "Test A",
                "category": "technical_issue",
                "pipeline": "support",
                "hs_ticket_priority": "HIGH",
                "hs_pipeline_stage": "1",
            },
            {
                "subject": "Bulk Tix B",
                "description": "Test B",
                "category": "billing",
                "pipeline": "support",
                "hs_ticket_priority": "LOW",
                "hs_pipeline_stage": "2",
            },
        ]
        mock_create_ticket.side_effect = [
            {"id": "TICKET_111", "properties": {"subject": "Bulk Tix A"}},
            {"id": "TICKET_222", "properties": {"subject": "Bulk Tix B"}},
        ]

        results = service.create_tickets(tickets_data)

        assert len(results) == 2
        assert results[0]["id"] == "TICKET_111"
        assert results[1]["id"] == "TICKET_222"
        assert mock_create_ticket.call_count == 2
