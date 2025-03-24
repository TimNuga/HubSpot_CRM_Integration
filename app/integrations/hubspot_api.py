import requests
from requests.exceptions import RequestException
from flask import current_app
from app.utils.rate_limit_handler import request_with_tenacity


class HubSpotAPI:
    """
    Low-level HubSpot integration for direct HTTP calls.
    """

    def __init__(self, token: str):
        self.token = token
        self.base_url = current_app.config.get(
            "HUBSPOT_API_BASE_URL", "https://api.hubapi.com"
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def find_contact_by_email(self, email: str):
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email}
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "phone"],
        }
        try:
            resp = request_with_tenacity(
                "POST", url, headers=self._headers(), json=payload, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("total", 0) > 0:
                return data["results"][0]
            return None
        except RequestException as e:
            current_app.logger.error("find_contact_by_email error: %s", str(e))
            raise

    def create_contact(self, properties: dict):
        url = f"{self.base_url}/crm/v3/objects/contacts"
        try:
            resp = request_with_tenacity(
                "POST",
                url,
                headers=self._headers(),
                json={"properties": properties},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("create_contact error: %s", str(e))
            raise

    def update_contact(self, contact_id: str, properties: dict):
        url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
        try:
            resp = request_with_tenacity(
                "PATCH",
                url,
                headers=self._headers(),
                json={"properties": properties},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("update_contact error: %s", str(e))
            raise

    def find_deal_by_name(self, deal_name: str):
        url = f"{self.base_url}/crm/v3/objects/deals/search"
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "dealname",
                            "operator": "EQ",
                            "value": deal_name,
                        }
                    ]
                }
            ],
            "properties": ["dealname", "amount", "dealstage"],
        }
        try:
            resp = request_with_tenacity(
                "POST", url, headers=self._headers(), json=payload, timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("total", 0) > 0:
                return data["results"][0]
            return None
        except RequestException as e:
            current_app.logger.error("find_deal_by_name error: %s", str(e))
            raise

    def create_deal(self, properties: dict):
        url = f"{self.base_url}/crm/v3/objects/deals"
        try:
            resp = request_with_tenacity(
                "POST",
                url,
                headers=self._headers(),
                json={"properties": properties},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("create_deal error: %s", str(e))
            raise

    def update_deal(self, deal_id: str, properties: dict):
        url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}"
        try:
            resp = request_with_tenacity(
                "PATCH",
                url,
                headers=self._headers(),
                json={"properties": properties},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("update_deal error: %s", str(e))
            raise

    def create_ticket(self, properties: dict):
        url = f"{self.base_url}/crm/v3/objects/tickets"
        try:
            resp = request_with_tenacity(
                "POST",
                url,
                headers=self._headers(),
                json={"properties": properties},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("create_ticket error: %s", str(e))
            raise

    def associate_contact_and_deal(self, contact_id: str, deal_id: str):
        url = f"{self.base_url}/crm/v3/associations/Deals/Contacts/batch/create"
        body = {
            "inputs": [{"from": {"id": str(deal_id)}, "to": {"id": str(contact_id)}}]
        }
        try:
            resp = request_with_tenacity(
                "POST", url, headers=self._headers(), json=body, timeout=10
            )
            resp.raise_for_status()
            return True
        except RequestException as e:
            current_app.logger.error("associate_contact_and_deal error: %s", str(e))
            raise

    def associate_ticket_with_contact(self, ticket_id: str, contact_id: str):
        url = f"{self.base_url}/crm/v3/associations/Tickets/Contacts/batch/create"
        body = {
            "inputs": [{"from": {"id": str(ticket_id)}, "to": {"id": str(contact_id)}}]
        }
        try:
            resp = request_with_tenacity(
                "POST", url, headers=self._headers(), json=body, timeout=10
            )
            resp.raise_for_status()
            return True
        except RequestException as e:
            current_app.logger.error("associate_ticket_with_contact error: %s", str(e))
            raise

    def associate_ticket_with_deal(self, ticket_id: str, deal_id: str):
        url = f"{self.base_url}/crm/v3/associations/Tickets/Deals/batch/create"
        body = {
            "inputs": [{"from": {"id": str(ticket_id)}, "to": {"id": str(deal_id)}}]
        }
        try:
            resp = request_with_tenacity(
                "POST", url, headers=self._headers(), json=body, timeout=10
            )
            resp.raise_for_status()
            return True
        except RequestException as e:
            current_app.logger.error("associate_ticket_with_deal error: %s", str(e))
            raise

    def get_new_objects(self, object_type: str, limit: int = 10, after: str = None):
        """
        Original logic for fetching new objects from HubSpot directly, if needed.
        Not used now for the local approach, but left for reference.
        """
        url = f"{self.base_url}/crm/v3/objects/{object_type}"
        params = {"limit": limit, "after": after, "sort": "-createdate"}
        try:
            resp = request_with_tenacity(
                "GET", url, headers=self._headers(), params=params, timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            current_app.logger.error("get_new_objects error: %s", str(e))
            raise
