import pytest
from marshmallow import ValidationError
from app.schemas.hubspot_schema import TicketSchema
from app.utils.constants import VALID_CATEGORIES


class TestTicketSchema:

    def test_ticket_schema_valid(self):
        data = {
            "subject": "Test Ticket",
            "description": "Something is broken",
            "category": VALID_CATEGORIES[0],  # pick an allowed category
            "pipeline": "support_pipeline",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1",
            "contact_id": "CONTACT_ABC",
            "deal_id": "DEAL_999",
        }
        result = TicketSchema().load(data)
        assert result["subject"] == "Test Ticket"
        assert result["category"] == VALID_CATEGORIES[0]
        assert result["contact_id"] == "CONTACT_ABC"
        assert result["deal_id"] == "DEAL_999"

    def test_ticket_schema_missing_fields(self):
        data = {
            "subject": "No Pipeline",
            "description": "Missing pipeline, category, etc.",
        }
        with pytest.raises(ValidationError) as exc_info:
            TicketSchema().load(data)
        errors = exc_info.value.messages
        # Expects 'category', 'pipeline', 'hs_ticket_priority', 'hs_pipeline_stage' to be missing
        assert "category" in errors
        assert "pipeline" in errors
        assert "hs_ticket_priority" in errors
        assert "hs_pipeline_stage" in errors

    def test_ticket_schema_invalid_category(self):
        """
        'category' must be in VALID_CATEGORIES.
        Let's try an invalid category.
        """
        data = {
            "subject": "Broken Stuff",
            "description": "We have an invalid category",
            "category": "not_valid",
            "pipeline": "support_pipeline",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1",
        }
        with pytest.raises(ValidationError) as exc_info:
            TicketSchema().load(data)
        errors = exc_info.value.messages
        assert "category" in errors

    def test_ticket_schema_extra_fields(self):
        """
        Since the schema does not allow unknown fields, extra fields should raise a ValidationError.
        """
        data = {
            "subject": "Extra Fields Ticket",
            "description": "Ticket with extra fields.",
            "category": VALID_CATEGORIES[0],
            "pipeline": "support_pipeline",
            "hs_ticket_priority": "HIGH",
            "hs_pipeline_stage": "1",
            "unknown_field": "should not be here",
        }
        with pytest.raises(ValidationError) as excinfo:
            TicketSchema().load(data)
        errors = excinfo.value.messages
        assert "unknown_field" in errors
