import pytest
from unittest.mock import patch, MagicMock
from app.hubspot_service import create_or_update_contact, create_ticket
from app.models import CreatedCRMObject
from app import db


@pytest.mark.usefixtures("db_session")
def test_store_local_crm_object(db_session):
    """
    Example: verifying that a local record is stored after creating a contact.
    """
    # Suppose we patch 'requests.post' to simulate HubSpot's API returning a new contact ID
    with patch("app.utils.rate_limit_handler.requests.request") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "CONTACT_123"}
        mock_post.return_value = mock_resp

        contact_id = create_or_update_contact(
            {
                "email": "test@example.com",
                "firstname": "Alice",
                "lastname": "Doe",
                "phone": "+1-555-1234",
            }
        )
        assert contact_id == "CONTACT_123"

    # Verify we created a local reference
    local_records = db_session.query(CreatedCRMObject).all()
    assert len(local_records) == 1
    assert local_records[0].object_id == "CONTACT_123"
    assert local_records[0].object_type == "contact"


@pytest.mark.usefixtures("db_session")
def test_create_ticket_with_deals(db_session):
    """
    Ensures that create_ticket can handle multiple deal associations.
    """
    with patch("app.utils.rate_limit_handler.requests.request") as mock_post:
        # Fake the ticket creation response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "TICKET_ABC"}
        mock_post.return_value = mock_resp

        ticket_id = create_ticket(
            ticket_data={
                "subject": "Billing Issue",
                "description": "Customer cannot pay",
                "category": "billing",
                "hs_pipeline": "support",
                "hs_ticket_priority": "HIGH",
                "hs_pipeline_stage": "1",
            },
            contact_id="CONTACT_123",
            deal_ids=["DEAL_789", "DEAL_456"],
        )
        assert ticket_id == "TICKET_ABC"

    # Validate local DB
    local_records = (
        db_session.query(CreatedCRMObject).filter_by(object_type="ticket").all()
    )
    assert len(local_records) == 1
    assert local_records[0].object_id == "TICKET_ABC"
