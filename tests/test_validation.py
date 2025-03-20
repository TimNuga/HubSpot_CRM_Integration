import pytest
import json
import requests_mock

@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_register_missing_contact_field(test_client):
    """
    Missing mandatory field: e.g., contact has no 'firstname'
    """
    payload = {
        "contact": {
            "email": "test@example.com",
            "lastname": "Doe",
            "phone": "12345"
        },
        "deals": [],
        "tickets": []
    }
    resp = test_client.post("/crm/register", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "CONTACT_VALIDATION_ERROR" in data["error"]["code"]
    assert "firstname" in data["error"]["details"]

@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_register_invalid_ticket_category(test_client):
    """
    Invalid category in ticket schema
    """
    payload = {
        "contact": {
            "email": "test@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "phone": "123-456-7890"
        },
        "tickets": [
            {
                "subject": "Test Ticket",
                "description": "Some desc",
                "category": "INVALID_CATEGORY",  # not in the valid list
                "pipeline": "support",
                "hs_ticket_priority": "HIGH",
                "hs_pipeline_stage": "1"
            }
        ]
    }
    resp = test_client.post("/crm/register", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "TICKET_VALIDATION_ERROR" in data["error"]["code"]
    assert "category" in data["error"]["details"]

@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_register_deal_amount_not_float(test_client):
    """
    'amount' should be float or int. Here we pass string => expect 400.
    """
    payload = {
        "contact": {
            "email": "test@example.com",
            "firstname": "Jane",
            "lastname": "Doe",
            "phone": "111-222-3333"
        },
        "deals": [
            {
                "dealname": "Test Deal",
                "amount": "NotANumber",  # invalid
                "dealstage": "appointmentscheduled"
            }
        ],
        "tickets": []
    }
    resp = test_client.post("/crm/register", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "DEAL_VALIDATION_ERROR" in data["error"]["code"]
    assert "amount" in data["error"]["details"]

@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_register_valid_data(test_client):
    """
    Everything correct => 200 and success.
    """
    payload = {
        "contact": {
            "email": "test@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "phone": "12345"
        },
        "deals": [
            {
                "dealname": "Test Deal",
                "amount": 1500.0,
                "dealstage": "appointmentscheduled"
            }
        ],
        "tickets": [
            {
                "subject": "Test Ticket",
                "description": "Test Desc",
                "category": "billing",
                "pipeline": "support",
                "hs_ticket_priority": "HIGH",
                "hs_pipeline_stage": "1"
            }
        ]
    }

    with requests_mock.Mocker() as m:
        # Mock token refresh endpoint
        m.post("https://api.hubapi.com/oauth/v1/token", json={
            "access_token": "MOCK_TOKEN",
            "refresh_token": "MOCK_REFRESH",
            "expires_in": 3600
        })
        # Mock contact search: no results so contact is created
        m.post("https://api.hubapi.com/crm/v3/objects/contacts/search", json={"results": []})
        # Mock contact creation
        m.post("https://api.hubapi.com/crm/v3/objects/contacts", json={"id": "CONTACT_123"})
        # Mock deal search: no results
        m.post("https://api.hubapi.com/crm/v3/objects/deals/search", json={"results": []})
        # Mock deal creation
        m.post("https://api.hubapi.com/crm/v3/objects/deals", json={"id": "DEAL_999"})
        # Mock ticket creation
        m.post("https://api.hubapi.com/crm/v3/objects/tickets", json={"id": "TICKET_ABC"})
    
        resp = test_client.post("/crm/register", json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "contact_id" in data
        assert "deal_ids" in data
        assert "ticket_ids" in data
