import pytest
from marshmallow import ValidationError
from app.schemas.hubspot_schema import ContactSchema


class TestContactSchema:

    def test_contact_schema_valid(self):
        data = {
            "email": "john@example.com",
            "firstname": "John",
            "lastname": "Doe",
            "phone": "1234567890",
        }
        result = ContactSchema().load(data)
        assert result["email"] == "john@example.com"
        assert result["firstname"] == "John"
        assert result["lastname"] == "Doe"
        assert result["phone"] == "1234567890"

    def test_contact_schema_missing_fields(self):
        data = {"email": "missingothers@example.com"}
        with pytest.raises(ValidationError) as exc_info:
            ContactSchema().load(data)
        errors = exc_info.value.messages
        # Should have errors for missing 'firstname', 'lastname', 'phone'
        assert "firstname" in errors
        assert "lastname" in errors
        assert "phone" in errors

    def test_contact_schema_invalid_email(self):
        data = {
            "email": "not-an-email",
            "firstname": "No Email",
            "lastname": "Test",
            "phone": "123",
        }
        with pytest.raises(ValidationError) as exc_info:
            ContactSchema().load(data)
        errors = exc_info.value.messages
        # 'email' should fail the Email validator
        assert "email" in errors

    def test_contact_schema_extra_fields(self):
        """
        Since the schema does not allow unknown fields, providing an extra field should cause a ValidationError.
        """
        data = {
            "email": "extra@example.com",
            "firstname": "Extra",
            "lastname": "Fields",
            "phone": "00000",
            "some_extra_field": "extra_value",
        }
        with pytest.raises(ValidationError) as excinfo:
            ContactSchema().load(data)
        errors = excinfo.value.messages
        assert "some_extra_field" in errors
