import pytest
import json
import requests_mock
from app.models import CreatedCRMObject
from datetime import datetime


@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_register_endpoint(test_client):
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

        # Mock search contact (no results => contact doesn't exist)
        m.post(
            "https://api.hubapi.com/crm/v3/objects/contacts/search",
            json={"results": []},
        )

        # Mock contact creation
        m.post(
            "https://api.hubapi.com/crm/v3/objects/contacts", json={"id": "CONTACT_123"}
        )

        # Mock deal search (no results => new)
        m.post(
            "https://api.hubapi.com/crm/v3/objects/deals/search", json={"results": []}
        )

        # Mock deal creation
        m.post("https://api.hubapi.com/crm/v3/objects/deals", json={"id": "DEAL_999"})

        # Mock ticket creation
        m.post(
            "https://api.hubapi.com/crm/v3/objects/tickets", json={"id": "TICKET_ABC"}
        )

        payload = {
            "contact": {
                "email": "test@example.com",
                "firstname": "Test",
                "lastname": "User",
                "phone": "123-456-7890",
            },
            "deals": [
                {
                    "dealname": "Test Deal",
                    "amount": 500,
                    "dealstage": "appointmentscheduled",
                }
            ],
            "tickets": [
                {
                    "subject": "Test Ticket",
                    "description": "Test Description",
                    "category": "technical_issue",
                    "hs_pipeline": "support",
                    "hs_ticket_priority": "HIGH",
                    "hs_pipeline_stage": "1",
                }
            ],
        }

        resp = test_client.post("/crm/register", json=payload)
        assert resp.status_code == 200
        data = json.loads(resp.data.decode())
        assert "contact_id" in data
        assert data["contact_id"] == "CONTACT_123"
        assert "deal_ids" in data
        assert "ticket_ids" in data


# @pytest.mark.usefixtures("test_app", "test_client", "db_session")
# def test_objects_endpoint(test_client, db_session):
#     """
#     Verifies the GET /crm/objects endpoint returns newly created local DB objects.
#     """
#     resp = test_client.get("/crm/objects")
#     assert resp.status_code == 200
#     data = json.loads(resp.data)
#     assert "new_objects" in data


@pytest.mark.usefixtures("test_app", "test_client", "db_session")
def test_pagination_flow(test_client, db_session):
    """
    Verifies that cursor-based pagination on /objects works as expected.
    """
    db_session.query(CreatedCRMObject).delete()
    db_session.commit()

    fixed_time = datetime.utcnow()
    records = []

    # Seeding test db with 25 local records
    for i in range(1, 26):
        record = CreatedCRMObject(
            object_id=f"OBJ_{i}",
            object_type="contact" if i % 2 == 0 else "deal",
            created_at=fixed_time,
        )
        records.append(record)

    db_session.add_all(records)
    db_session.commit()

    count = db_session.query(CreatedCRMObject).count()
    assert count == 25, f"Expected 25 records, but found {count}"

    # Requesting first page with limit=10
    resp = test_client.get("/crm/objects?limit=10")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "new_objects" in data
    assert "next_after" in data

    first_page = data["new_objects"]
    next_after = data["next_after"]
    assert len(first_page) == 10, f"Expected 10, got {len(first_page)}"
    assert next_after is not None, "Should have next_after for subsequent pages"

    # Requesting second page
    resp2 = test_client.get(f"/crm/objects?limit=10&after={next_after}")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    second_page = data2["new_objects"]
    next_after2 = data2["next_after"]
    assert len(second_page) == 10, f"Expected 10, got {len(second_page)}"

    # Requesting final page
    resp3 = test_client.get(f"/crm/objects?limit=10&after={next_after2}")
    assert resp3.status_code == 200
    data3 = resp3.get_json()
    final_page = data3["new_objects"]
    final_next_after = data3["next_after"]
    assert (
        final_next_after is None
    ), "No more items remain, so next_after should be null"
