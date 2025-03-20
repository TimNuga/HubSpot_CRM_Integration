import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from ..hubspot_service import (
    create_or_update_contact,
    create_or_update_deal,
    create_ticket,
    retrieve_new_objects
)
from app.schemas import ContactSchema, DealSchema, TicketSchema

crm_blueprint = Blueprint("crm", __name__)
logger = logging.getLogger(__name__)

contact_schema = ContactSchema()
deal_schema = DealSchema()
ticket_schema = TicketSchema()

@crm_blueprint.route("/register", methods=["POST"])
def register():
    """
    1) Create or update a contact
    2) Create/update deals associated with the contact
    3) Create (always new) tickets associated with contact + deals
    Example payload:
    {
      "contact": {...},
      "deals": [...],
      "tickets": [...]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_PAYLOAD",
                "message": "Request body must be valid JSON."
            }
        }), 400

    contact_data = data.get("contact")
    deals_data = data.get("deals", [])
    tickets_data = data.get("tickets", [])

    if not contact_data:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_CONTACT",
                "message": "Missing 'contact' data."
            }
        }), 400

    try:
        validated_contact = contact_schema.load(contact_data)
    except ValidationError as e:
        logger.warning("Contact validation error: %s", e.messages)
        return jsonify({
            "success": False,
            "error": {
                "code": "CONTACT_VALIDATION_ERROR",
                "details": e.messages
            }
        }), 400

    validated_deals = []
    for idx, deal in enumerate(deals_data):
        try:
            val_deal = deal_schema.load(deal)
            validated_deals.append(val_deal)
        except ValidationError as e:
            logger.warning("Deal #%s validation error: %s", idx, e.messages)
            return jsonify({
                "success": False,
                "error": {
                    "code": "DEAL_VALIDATION_ERROR",
                    "details": e.messages,
                    "deal_index": idx
                }
            }), 400


    validated_tickets = []
    for idx, ticket in enumerate(tickets_data):
        try:
            val_ticket = ticket_schema.load(ticket)
            validated_tickets.append(val_ticket)
        except ValidationError as e:
            logger.warning("Ticket #%s validation error: %s", idx, e.messages)
            return jsonify({
                "success": False,
                "error": {
                    "code": "TICKET_VALIDATION_ERROR",
                    "details": e.messages,
                    "ticket_index": idx
                }
            }), 400

    logger.info("All data validated. Proceeding with create/update logic...")

    try:
        contact_id = create_or_update_contact(validated_contact)
        deal_ids = []
        for d in validated_deals:
            d_id = create_or_update_deal(d, contact_id)
            deal_ids.append(d_id)
        ticket_ids = []
        for t in validated_tickets:
            t_id = create_ticket(t, contact_id, deal_ids)
            ticket_ids.append(t_id)

        return jsonify({
            "success": True,
            "message": "Contact, Deal(s), and Ticket(s) processed successfully.",
            "contact_id": contact_id,
            "deal_ids": deal_ids,
            "ticket_ids": ticket_ids
        }), 200
    except Exception as e:
        logger.error("Error processing CRM data: %s", str(e), exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "CRM_PROCESSING_ERROR",
                "message": str(e)
            }
        }), 500


# @crm_blueprint.route("/objects", methods=["GET"])
# def get_new_objects():
#     """
#     Returns newly created/updated objects from local DB.
#     You could also add pagination here if desired (e.g., /objects?page=1&limit=10).
#     """
#     try:
#         data = retrieve_new_objects()
#         return jsonify({"new_objects": data}), 200
#     except Exception as e:
#         logger.error("Error retrieving new objects: %s", str(e))
#         return jsonify({"error": str(e)}), 500

@crm_blueprint.route("/objects", methods=["GET"])
def get_new_objects():
    """
    Returns newly created/updated objects from local DB in descending order.
    Cursor-based pagination via:
      - /objects?limit=10&after=123
    """
    try:
        limit = int(request.args.get("limit", 10))
        after_param = request.args.get("after")
        after = after_param if after_param is not None else None

        data, next_after = retrieve_new_objects(limit=limit, after=after)

        return jsonify({
            "new_objects": data,
            "next_after": next_after
        }), 200
    except Exception as e:
        logger.error("Error retrieving new objects: %s", str(e))
        return jsonify({"error": str(e)}), 500