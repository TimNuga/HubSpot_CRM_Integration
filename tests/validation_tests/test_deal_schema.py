import pytest
from marshmallow import ValidationError
from app.schemas.hubspot_schema import DealSchema


class TestDealSchema:

    def test_deal_schema_valid(self):
        data = {
            "dealname": "Big Deal",
            "amount": 1000.50,
            "dealstage": "appointmentscheduled",
            "contact_id": "CONTACT_123",
        }
        result = DealSchema().load(data)
        assert result["dealname"] == "Big Deal"
        assert result["amount"] == 1000.50
        assert result["dealstage"] == "appointmentscheduled"
        assert result["contact_id"] == "CONTACT_123"

    def test_deal_schema_missing_fields(self):
        data = {"dealname": "Missing Stage", "amount": 500}
        with pytest.raises(ValidationError) as exc_info:
            DealSchema().load(data)
        errors = exc_info.value.messages
        # 'dealstage' is required
        assert "dealstage" in errors

    def test_deal_schema_invalid_amount(self):
        """
        Marshmallow should fail if 'amount' can't be cast to float.
        """
        data = {
            "dealname": "Invalid Amount",
            "amount": "NotANumber",
            "dealstage": "appointmentscheduled",
        }
        with pytest.raises(ValidationError) as exc_info:
            DealSchema().load(data)
        errors = exc_info.value.messages
        assert "amount" in errors
