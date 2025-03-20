import time
import requests
import logging
from flask import current_app
from app.extensions import db
from app.models import CreatedCRMObject
from app.utils.rate_limit_handler import request_with_tenacity
# from dateutil.parser import isoparse
from datetime import datetime

logger = logging.getLogger(__name__)

def get_or_refresh_access_token():
    """
    Retrieves or refreshes HubSpot access token using refresh token if the in-memory token is None.
    You'd store expiry in production to refresh proactively.
    """
    config = current_app.config
    now = int(time.time())
    expires_at = config.get("HUBSPOT_TOKEN_EXPIRES_AT", 0)
    buffer_sec = config.get("TOKEN_REFRESH_BUFFER", 60)

    # If we have a token and it's not near expiry, just return it
    if config["HUBSPOT_ACCESS_TOKEN"] and (now < expires_at - buffer_sec):
        return config["HUBSPOT_ACCESS_TOKEN"]

    logger.info("Token is expired or close to expiry. Refreshing...")

    # Refresh the token
    payload = {
        "grant_type": "refresh_token",
        "client_id": config["HUBSPOT_CLIENT_ID"],
        "client_secret": config["HUBSPOT_CLIENT_SECRET"],
        "refresh_token": config["HUBSPOT_REFRESH_TOKEN"],
    }

    resp = requests.post(config["HUBSPOT_OAUTH_TOKEN_URL"], data=payload, timeout=30)
    if resp.status_code != 200:
        logger.error("Failed to refresh HubSpot token: %s", resp.text)
        raise Exception("Unable to obtain HubSpot access token")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    new_refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 0)

    if not access_token or not expires_in:
        logger.error("Token response missing required fields: %s", token_data)
        raise Exception("Invalid token response from HubSpot")
    
    new_expires_at = now + expires_in

    config["HUBSPOT_ACCESS_TOKEN"] = access_token

    if new_refresh_token:
        config["HUBSPOT_REFRESH_TOKEN"] = new_refresh_token
    
    config["HUBSPOT_TOKEN_EXPIRES_AT"] = new_expires_at

    logger.info("Refreshed token. Expires in %s seconds (at %s)", expires_in, new_expires_at)
    return access_token

def hubspot_headers():
    token = get_or_refresh_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def create_or_update_contact(contact_data):
    """
    Creates or updates a HubSpot contact. Returns the HubSpot contact ID.
    Also logs the creation/update in local DB.
    """
    email = contact_data.get("email")
    if not email:
        raise ValueError("Contact data must include 'email'.")

    search_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }],
        "properties": ["email"],
        "limit": 1
    }
    search_resp = request_with_tenacity(
        "POST", 
        search_url, 
        headers=hubspot_headers(), 
        json=payload,
        timeout=30
    )

    if search_resp.status_code == 200:
        results = search_resp.json().get("results", [])
        base_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/contacts"

        if results:
            contact_id = results[0]["id"]
            update_url = f"{base_url}/{contact_id}"
            update_payload = {"properties": contact_data}
            update_resp = request_with_tenacity(
                "PATCH", 
                update_url, 
                headers=hubspot_headers(), 
                json=update_payload
            )
            _store_local_crm_object(contact_id, "contact")
            logger.info("Updated contact %s", contact_id)
            return contact_id
        else:
            # Create new contact
            create_url = base_url
            create_payload = {"properties": contact_data}
            create_resp = request_with_tenacity(
                "POST",
                create_url,
                headers=hubspot_headers(),
                json=create_payload
            )
            new_id = create_resp.json()["id"]
            _store_local_crm_object(new_id, "contact")
            logger.info("Created new contact %s", new_id)
            return new_id
    else:
        logger.error("Search contact failed: %s", search_resp.text)
        search_resp.raise_for_status()

def get_contacts_from_hubspot(limit=20, after=None):
    """
    Fetches a page of contacts from HubSpot using cursor-based pagination.
    """
    base_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/contacts"
    params = {
        "limit": limit,
        "after": after,
        "properties": "email,firstname,lastname,phone",
        "archived": "false"
    }
    resp = request_with_tenacity("GET", base_url, headers=hubspot_headers(), params=params)
    data = resp.json()
    results = data.get("results", [])
    paging = data.get("paging", {})
    next_after = paging.get("next", {}).get("after")
    return results, next_after


def create_or_update_deal(deal_data, contact_id):
    """
    Creates or updates a deal in HubSpot. Returns the deal ID.
    Associates the deal with the provided contact.
    """
    deal_name = deal_data.get("dealname")
    if not deal_name:
        raise ValueError("Deal must include 'dealname'.")

    search_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/deals/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "dealname",
                "operator": "EQ",
                "value": deal_name
            }]
        }],
        "limit": 1
    }
    search_resp = request_with_tenacity("POST", search_url, headers=hubspot_headers(), json=payload)
    if search_resp.status_code != 200:
        raise Exception(f"Failed to search deal: {search_resp.text}")

    results = search_resp.json().get("results", [])
    base_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/deals"

    # Associate structure
    associations = [
        {
            "to": {"id": contact_id},
            "types": [{
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 3  # typical contact<->deal
            }]
        }
    ]

    if results:
        # Update existing
        deal_id = results[0]["id"]
        update_url = f"{base_url}/{deal_id}"
        update_payload = {
            "properties": deal_data,
            "associations": associations
        }
        update_resp = request_with_tenacity("PATCH", update_url, headers=hubspot_headers(), json=update_payload)
        if update_resp.status_code not in [200, 201]:
            raise Exception(f"Failed to update deal: {update_resp.text}")
        logger.info("Updated deal %s", deal_id)
        _store_local_crm_object(deal_id, "deal")
        return deal_id
    else:
        # Create new
        create_payload = {
            "properties": deal_data,
            "associations": associations
        }
        create_resp = requests.post(base_url, json=create_payload, headers=hubspot_headers(), timeout=30)
        if create_resp.status_code not in [200, 201]:
            raise Exception(f"Failed to create deal: {create_resp.text}")
        deal_id = create_resp.json()["id"]
        logger.info("Created new deal %s", deal_id)
        _store_local_crm_object(deal_id, "deal")
        return deal_id

def create_ticket(ticket_data, contact_id, deal_ids):
    """
    Creates a ticket in HubSpot. Always creates a new ticket.
    Associates it with the contact and deals.
    """
    base_url = f"{current_app.config['HUBSPOT_API_BASE_URL']}/crm/v3/objects/tickets"
    associations = [
        {
            "to": {"id": contact_id},
            "types": [{
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 15  # typical contact<->ticket
            }]
        }
    ]
    # Deals -> ticket
    for d_id in deal_ids:
        associations.append({
            "to": {"id": d_id},
            "types": [{
                "associationCategory": "HUBSPOT_DEFINED",
                "associationTypeId": 26  # typical deal<->ticket
            }]
        })

    payload = {
        "properties": ticket_data,
        "associations": associations
    }
    resp = request_with_tenacity("POST", base_url, headers=hubspot_headers(), json=payload)
    if resp.status_code not in [200, 201]:
        raise Exception(f"Failed to create ticket: {resp.text}")
    ticket_id = resp.json()["id"]
    logger.info("Created new ticket %s", ticket_id)
    _store_local_crm_object(ticket_id, "ticket")
    return ticket_id

def _store_local_crm_object(obj_id, obj_type):
    """
    Persists a reference of the created/updated CRM object in PostgreSQL.
    """
    crm_obj = CreatedCRMObject(object_id=obj_id, object_type=obj_type)
    db.session.add(crm_obj)
    db.session.commit()

def retrieve_new_objects(limit=10, after=None):
    """
    Retrieves newly created CRM objects in descending order using compound cursor-based pagination.
    The cursor format is "<created_at_iso>:<id>".
    """
    base_query = CreatedCRMObject.query.order_by(CreatedCRMObject.id.desc())

    if after is not None:
        try:
            # Use rsplit with maxsplit=1 to split on the last colon only.
            last_created_at_str, last_id_str = after.rsplit(":", 1)
            last_created_at = datetime.fromisoformat(last_created_at_str)
            last_id = int(last_id_str)
            # Use a compound filter: 
            base_query = base_query.filter(
                (CreatedCRMObject.created_at < last_created_at) |
                ((CreatedCRMObject.created_at == last_created_at) & (CreatedCRMObject.id < last_id))
            )
        except Exception as e:
            raise Exception("Invalid cursor format. Expected 'created_at_iso:id'") from e

    # Fetch one extra record to determine if there's a next page.
    rows = base_query.limit(limit + 1).all()

    if len(rows) > limit:
        last_row = rows[-1]
        # Construct the compound cursor
        next_after = f"{last_row.created_at.isoformat()}:{last_row.id}"
        rows = rows[:-1]
    else:
        next_after = None

    results = [{
        "id": r.id,
        "object_id": r.object_id,
        "object_type": r.object_type,
        "created_at": r.created_at.isoformat(),
    } for r in rows]

    return results, next_after



# def retrieve_new_objects():
#     """
#     Example: Return objects from local DB. You can also directly query HubSpot with 'createdate'.
#     For demonstration, we rely on local DB that tracks newly created or updated items.
#     """
#     rows = CreatedCRMObject.query.order_by(CreatedCRMObject.created_at.desc()).all()
#     results = []
#     for r in rows:
#         results.append({
#             "id": r.id,
#             "object_id": r.object_id,
#             "object_type": r.object_type,
#             "created_at": r.created_at.isoformat(),
#         })
#     return results