from flask import current_app
from requests.exceptions import RequestException
import datetime

from app.models import CreatedCRMObject, db
from app.utils.errors import BaseError
from .oauth_service import HubspotOAuthService
from ..integrations.hubspot_api import HubSpotAPI
from typing import List, Dict


class HubSpotService:
    """
    Encapsulates business logic for upserting contacts/deals,
    creating tickets, and retrieving new objects from local DB.
    """

    def __init__(self):
        self.oauth_service = HubspotOAuthService()

    def _api_client(self) -> HubSpotAPI:
        token = self.oauth_service.get_access_token()
        return HubSpotAPI(token)

    def upsert_contact(self, contact_data: dict) -> dict:
        """
        If the contact doesn't exist, create it; else update the existing record.
        Then store or update local CreatedCRMObject to track it as 'contacts'.
        """
        api = self._api_client()
        existing = api.find_contact_by_email(contact_data["email"])
        if existing:
            contact_id = existing["id"]
            updated = api.update_contact(contact_id, contact_data)
            self._store_created_crm_object(
                external_id=contact_id,
                object_type="contacts",
                name=updated["properties"].get("email", ""),
            )
            return updated
        else:
            created = api.create_contact(contact_data)
            contact_id = created["id"]
            self._store_created_crm_object(
                external_id=contact_id,
                object_type="contacts",
                name=created["properties"].get("email", ""),
            )
            return created

    def upsert_deal(self, deal_data: dict) -> dict:
        """
        If the deal doesn't exist, create it; else update the existing record.
        Also, associate with contact if contact_id is present.
        Then store or update local CreatedCRMObject as 'deals'.
        """
        api = self._api_client()
        existing = api.find_deal_by_name(deal_data["dealname"])
        if existing:
            deal_id = existing["id"]
            updated = api.update_deal(deal_id, deal_data)
            if "contact_id" in deal_data:
                api.associate_contact_and_deal(deal_data["contact_id"], deal_id)
            self._store_created_crm_object(
                external_id=deal_id,
                object_type="deals",
                name=updated["properties"].get("dealname", ""),
            )
            return updated
        else:
            created = api.create_deal(deal_data)
            deal_id = created["id"]
            if "contact_id" in deal_data:
                api.associate_contact_and_deal(deal_data["contact_id"], deal_id)
            self._store_created_crm_object(
                external_id=deal_id,
                object_type="deals",
                name=created["properties"].get("dealname", ""),
            )
            return created

    def create_ticket(self, ticket_data: dict) -> dict:
        """
        Always creates a new ticket, never updates existing ones.
        If contact_id and/or deal_id exist, associate them.
        Then store local CreatedCRMObject as 'tickets'.
        """
        api = self._api_client()
        created = api.create_ticket(ticket_data)
        ticket_id = created["id"]

        if "contact_id" in ticket_data:
            try:
                api.associate_ticket_with_contact(ticket_id, ticket_data["contact_id"])
            except RequestException as e:
                current_app.logger.warning(
                    "Failed to associate ticket with contact: %s", str(e)
                )

        if "deal_id" in ticket_data:
            try:
                api.associate_ticket_with_deal(ticket_id, ticket_data["deal_id"])
            except RequestException as e:
                current_app.logger.warning(
                    "Failed to associate ticket with deal: %s", str(e)
                )

        self._store_created_crm_object(
            external_id=ticket_id,
            object_type="tickets",
            name=created["properties"].get("subject", ""),
        )
        return created

    def upsert_deals(self, deals_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Accepts a list of deals, upserts each one, returns a list of results.
        """
        results = []
        for deal_data in deals_data:
            single_result = self.upsert_deal(deal_data)
            results.append(single_result)
        return results

    def create_tickets(
        self, tickets_data: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Accepts a list of tickets, creates each one, returns a list of results.
        """
        results = []
        for ticket_data in tickets_data:
            single_ticket = self.create_ticket(ticket_data)
            results.append(single_ticket)
        return results

    def get_new_objects_from_db(self, object_type: str, page: int = 1, limit: int = 10):
        """
        Retrieves newly created CRM objects from local DB, filtered by object_type if provided.
        Returns a list of local records and the total count.
        Pagination is offset-based: offset = (page-1)*limit
        """
        query = CreatedCRMObject.query
        if object_type:
            query = query.filter_by(object_type=object_type)

        total = query.count()
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()

        # Convert each CreatedCRMObject to a dict
        data = []
        for obj in results:
            data.append(
                {
                    "id": obj.id,
                    "external_id": obj.external_id,
                    "object_type": obj.object_type,
                    "name": obj.name,
                    "created_date": obj.created_date.isoformat(),
                    "updated_date": obj.updated_date.isoformat(),
                }
            )

        return data, total

    # __OPTIONAL: STILL CALL HUBSPOT
    def get_new_objects(
        self, object_type: str, limit: int = 10, after: str = None
    ) -> dict:
        """
        If you still want to fetch new objects from HubSpot directly,
        you can use this. Not currently used by the controller,
        but left for reference.
        """
        api = self._api_client()
        return api.get_new_objects(object_type, limit=limit, after=after)

    def _store_created_crm_object(self, external_id: str, object_type: str, name: str):
        """
        Insert or update a record in CreatedCRMObject for the newly
        created/updated CRM object. If it already exists by external_id,
        update the name/updated_date.
        """
        existing = CreatedCRMObject.query.filter_by(
            external_id=external_id, object_type=object_type
        ).first()
        if existing:
            existing.name = name
            existing.updated_date = datetime.datetime.utcnow()
        else:
            new_obj = CreatedCRMObject(
                external_id=external_id,
                object_type=object_type,
                name=name,
            )
            db.session.add(new_obj)

        db.session.commit()
