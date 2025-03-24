from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError

from app.services.hubspot_service import HubSpotService
from app.schemas.hubspot_schema import ContactSchema, DealSchema, TicketSchema
from app.utils.api_responses import success_response, error_response
from app.utils.errors import BadRequestError

hubspot_bp = Blueprint("hubspot", __name__)


@hubspot_bp.route("/contacts", methods=["POST", "PUT"])
def upsert_contact():
    """
    Create or update a HubSpot contact. Also updates local DB with CreatedCRMObject.
    """
    try:
        data = request.get_json() or {}
        schema = ContactSchema()
        validated = schema.load(data)

        service = HubSpotService()
        contact = service.upsert_contact(validated)

        current_app.logger.info("Upserted contact for email=%s", validated["email"])
        return jsonify(success_response({"contact": contact})), 200

    except ValidationError as ve:
        current_app.logger.warning(
            "Validation error in upsert_contact: %s", ve.messages
        )
        raise BadRequestError(
            message="Contact validation failed.", verboseMessage=str(ve.messages)
        )
    except Exception as e:
        current_app.logger.exception("Error upserting contact.")
        return jsonify(error_response(str(e), "Failed to upsert contact", 500)), 500


@hubspot_bp.route("/deals", methods=["POST", "PUT"])
def upsert_deal():
    """
    Create or update a HubSpot deal. Also updates local DB with CreatedCRMObject.
    """
    try:
        data = request.get_json() or {}
        schema = DealSchema()
        validated = schema.load(data)

        service = HubSpotService()
        deal = service.upsert_deal(validated)

        current_app.logger.info("Upserted deal for dealname=%s", validated["dealname"])
        return jsonify(success_response({"deal": deal})), 200

    except ValidationError as ve:
        current_app.logger.warning("Validation error in upsert_deal: %s", ve.messages)
        raise BadRequestError(
            message="Deal validation failed.", verboseMessage=str(ve.messages)
        )
    except Exception as e:
        current_app.logger.exception("Error upserting deal.")
        return jsonify(error_response(str(e), "Failed to upsert deal", 500)), 500


@hubspot_bp.route("/tickets", methods=["POST"])
def create_ticket():
    """
    Always create a new ticket in HubSpot (never update). Also creates local DB entry in CreatedCRMObject.
    """
    try:
        data = request.get_json() or {}
        schema = TicketSchema()
        validated = schema.load(data)

        service = HubSpotService()
        ticket = service.create_ticket(validated)

        current_app.logger.info("Created ticket subject=%s", validated["subject"])
        return jsonify(success_response({"ticket": ticket}, status_code=201)), 201

    except ValidationError as ve:
        current_app.logger.warning("Validation error creating ticket: %s", ve.messages)
        raise BadRequestError(
            message="Ticket validation failed.", verboseMessage=str(ve.messages)
        )
    except Exception as e:
        current_app.logger.exception("Error creating ticket.")
        return jsonify(error_response(str(e), "Failed to create ticket", 500)), 500


@hubspot_bp.route("/new-crm-objects", methods=["GET"])
def get_new_crm_objects():
    """
    Retrieve newly created CRM objects from the local DB, filtered by objectType.
    Pagination is offset-based or page-based here, for example:
      ?objectType=contacts|deals|tickets
      &page=1
      &limit=10
    """
    try:
        object_type = request.args.get("objectType", "").lower() or None
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))

        service = HubSpotService()
        results, total = service.get_new_objects_from_db(object_type, page, limit)

        response_data = {
            "page": page,
            "limit": limit,
            "total": total,
            "results": results,
        }
        current_app.logger.info(
            "Fetched new CRM objects for type=%s page=%d limit=%d",
            object_type,
            page,
            limit,
        )
        return jsonify(success_response(response_data)), 200

    except Exception as e:
        current_app.logger.exception("Error retrieving new CRM objects.")
        return (
            jsonify(error_response(str(e), "Failed to retrieve new CRM objects", 500)),
            500,
        )

    @hubspot_bp.route("/deals/bulk", methods=["POST", "PUT"])
    def upsert_bulk_deals():
        """
        Create or update multiple deals in a single request.
        Expects JSON like: { "deals": [ {deal1}, {deal2}, ... ] }
        """
        try:
            data = request.get_json() or {}
            deals_data = data.get("deals", [])
            # Validate an array of deals
            schema = DealSchema(many=True)
            validated_deals = schema.load(deals_data)

            service = HubSpotService()
            results = service.upsert_deals(validated_deals)

            current_app.logger.info("Bulk upserted %d deals.", len(results))
            return jsonify(success_response({"deals": results})), 200

        except ValidationError as ve:
            current_app.logger.warning(
                "Validation error in upsert_bulk_deals: %s", ve.messages
            )
            raise BadRequestError(
                message="Bulk deals validation failed.", verboseMessage=str(ve.messages)
            )
        except Exception as e:
            current_app.logger.exception("Error bulk-upserting deals.")
            return (
                jsonify(error_response(str(e), "Failed to bulk upsert deals", 500)),
                500,
            )

    @hubspot_bp.route("/tickets/bulk", methods=["POST"])
    def create_bulk_tickets():
        """
        Create multiple tickets in a single request.
        Expects JSON like: { "tickets": [ {ticket1}, {ticket2}, ... ] }
        """
        try:
            data = request.get_json() or {}
            tickets_data = data.get("tickets", [])
            schema = TicketSchema(many=True)
            validated_tickets = schema.load(tickets_data)

            service = HubSpotService()
            results = service.create_tickets(validated_tickets)

            current_app.logger.info("Bulk created %d tickets.", len(results))
            return jsonify(success_response({"tickets": results}, status_code=201)), 201

        except ValidationError as ve:
            current_app.logger.warning(
                "Validation error in create_bulk_tickets: %s", ve.messages
            )
            raise BadRequestError(
                message="Bulk tickets validation failed.",
                verboseMessage=str(ve.messages),
            )
        except Exception as e:
            current_app.logger.exception("Error bulk-creating tickets.")
            return (
                jsonify(error_response(str(e), "Failed to bulk create tickets", 500)),
                500,
            )
