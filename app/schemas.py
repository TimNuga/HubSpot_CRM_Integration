from marshmallow import Schema, fields, ValidationError, validate

VALID_CATEGORIES = [
    "general_inquiry",
    "technical_issue",
    "billing",
    "service_request",
    "meeting",
]


class ContactSchema(Schema):
    email = fields.Email(required=True)
    firstname = fields.Str(required=True)
    lastname = fields.Str(required=True)
    phone = fields.Str(required=True)


class DealSchema(Schema):
    dealname = fields.Str(required=True)
    amount = fields.Float(required=True)
    dealstage = fields.Str(required=True)


class TicketSchema(Schema):
    subject = fields.Str(required=True)
    description = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(VALID_CATEGORIES))
    hs_pipeline = fields.Str(required=True)
    hs_ticket_priority = fields.Str(required=True)
    hs_pipeline_stage = fields.Str(required=True)
