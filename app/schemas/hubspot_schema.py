from marshmallow import Schema, fields, validate
from app.utils.constants import VALID_CATEGORIES


class ContactSchema(Schema):
    """
    Mandatory fields: email, firstname, lastname, phone
    Additional fields accepted dynamically.
    """

    email = fields.Email(required=True)
    firstname = fields.Str(required=True)
    lastname = fields.Str(required=True)
    phone = fields.Str(required=True)


class DealSchema(Schema):
    """
    Mandatory fields: dealname, amount, dealstage
    Additional fields accepted, e.g., contact_id for associations.
    """

    dealname = fields.Str(required=True)
    amount = fields.Float(required=True)
    dealstage = fields.Str(required=True)
    contact_id = fields.Str(required=False)  # optional for associating


class TicketSchema(Schema):
    """
    Mandatory fields:
      subject, description, category, pipeline,
      hs_ticket_priority, hs_pipeline_stage
    Additional fields accepted: contact_id, deal_id for association, etc.
    """

    subject = fields.Str(required=True)
    description = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(VALID_CATEGORIES))
    pipeline = fields.Str(required=True)
    hs_ticket_priority = fields.Str(required=True)
    hs_pipeline_stage = fields.Str(required=True)
    contact_id = fields.Str(required=False)
    deal_id = fields.Str(required=False)
