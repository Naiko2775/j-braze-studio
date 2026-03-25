from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base import BaseConnector

logger = logging.getLogger(__name__)


class SalesforceMarketingCloudConnector(BaseConnector):
    """Connecteur pour Salesforce Marketing Cloud (SFMC).

    Utilise l'API REST de SFMC avec authentification OAuth2.
    Config requise : client_id, client_secret, subdomain
    """

    def __init__(self, config: dict[str, Any]):
        self._access_token: str | None = None
        self._token_expiry: datetime | None = None
        super().__init__(config)

    @property
    def platform_name(self) -> str:
        return "salesforce_marketing_cloud"

    def _validate_config(self) -> None:
        required = ["client_id", "client_secret", "subdomain"]
        missing = [k for k in required if k not in self.config]
        if missing:
            raise ValueError(
                f"SFMC connector requires {', '.join(missing)} in config"
            )

    @property
    def _base_url(self) -> str:
        return f"https://{self.config['subdomain']}.rest.marketingcloudapis.com"

    @property
    def _auth_url(self) -> str:
        return f"https://{self.config['subdomain']}.auth.marketingcloudapis.com/v2/token"

    def _authenticate(self) -> None:
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
        }
        if "account_id" in self.config:
            payload["account_id"] = self.config["account_id"]

        response = requests.post(self._auth_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 1080)
        from datetime import timedelta
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

    @property
    def _headers(self) -> dict[str, str]:
        self._authenticate()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{self._base_url}/{endpoint}"
        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _post(self, endpoint: str, payload: dict | None = None) -> dict:
        url = f"{self._base_url}/{endpoint}"
        response = requests.post(url, headers=self._headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> bool:
        try:
            self._authenticate()
            return True
        except requests.RequestException:
            return False

    def fetch_contacts(self, limit: int | None = None, offset: int = 0) -> list[Contact]:
        contacts = []
        page = 1
        page_size = min(limit or 2500, 2500)

        de_key = self.config.get("contacts_de_key", "Subscribers")

        while True:
            try:
                data = self._get(
                    f"data/v1/customobjectdata/key/{de_key}/rowset",
                    params={"$page": page, "$pageSize": page_size},
                )
            except requests.RequestException:
                data = self._fetch_contacts_via_contacts_api(page, page_size)

            items = data.get("items", [])
            if not items:
                break

            for raw in items:
                contact = self._parse_contact(raw)
                contacts.append(contact)

            if limit and len(contacts) >= limit:
                contacts = contacts[:limit]
                break

            if len(items) < page_size:
                break

            page += 1

        logger.info(f"Fetched {len(contacts)} contacts from SFMC")
        return contacts

    def _fetch_contacts_via_contacts_api(self, page: int, page_size: int) -> dict:
        try:
            return self._get(
                "contacts/v1/contacts",
                params={"$page": page, "$pageSize": page_size},
            )
        except requests.RequestException:
            logger.warning("Could not fetch contacts via Contacts API")
            return {"items": []}

    def _parse_contact(self, raw: dict[str, Any]) -> Contact:
        keys = raw.get("keys", {})
        values = raw.get("values", {})

        custom_attrs = []
        standard_fields = {
            "EmailAddress", "FirstName", "LastName", "Phone",
            "Country", "City", "Gender", "DateOfBirth", "Language",
            "SubscriberKey", "Status",
        }

        for key, value in values.items():
            if key not in standard_fields and value is not None:
                attr_type = "string"
                if isinstance(value, bool):
                    attr_type = "boolean"
                elif isinstance(value, (int, float)):
                    attr_type = "number"
                custom_attrs.append(ContactAttribute(key=key, value=value, type=attr_type))

        subscriber_key = keys.get("SubscriberKey", values.get("SubscriberKey", str(uuid4())))

        email_subscribe = "subscribed"
        status = values.get("Status", "Active")
        if status in ("Unsubscribed", "Held", "Bounced"):
            email_subscribe = "unsubscribed"

        return Contact(
            external_id=str(subscriber_key),
            email=values.get("EmailAddress") or keys.get("EmailAddress"),
            phone=values.get("Phone"),
            first_name=values.get("FirstName"),
            last_name=values.get("LastName"),
            language=values.get("Language"),
            country=values.get("Country"),
            city=values.get("City"),
            gender=values.get("Gender"),
            date_of_birth=values.get("DateOfBirth"),
            email_subscribe=email_subscribe,
            custom_attributes=custom_attrs,
            created_at=_parse_datetime(values.get("CreatedDate")),
            updated_at=_parse_datetime(values.get("ModifiedDate")),
            source_id=str(subscriber_key),
            source_platform="salesforce_marketing_cloud",
        )

    def fetch_segments(self) -> list[Segment]:
        segments = []
        try:
            data = self._get("contacts/v1/lists", params={"$page": 1, "$pageSize": 50})
            for raw in data.get("items", []):
                segment = Segment(
                    id=str(raw.get("id", uuid4())),
                    name=raw.get("name", ""),
                    description=raw.get("description"),
                    contact_ids=[],
                    source_id=str(raw.get("id")),
                    source_platform="salesforce_marketing_cloud",
                    created_at=_parse_datetime(raw.get("createdDate")),
                    updated_at=_parse_datetime(raw.get("modifiedDate")),
                )

                try:
                    subs = self._get(
                        f"contacts/v1/lists/{raw['id']}/subscriptions",
                        params={"$page": 1, "$pageSize": 500},
                    )
                    segment.contact_ids = [
                        str(s.get("subscriberKey")) for s in subs.get("items", [])
                    ]
                except requests.RequestException:
                    logger.warning(f"Could not fetch subscribers for list {raw.get('id')}")

                segments.append(segment)
        except requests.RequestException:
            logger.warning("Could not fetch lists from SFMC")

        logger.info(f"Fetched {len(segments)} segments from SFMC")
        return segments

    def fetch_templates(self) -> list[EmailTemplate]:
        templates = []
        try:
            data = self._get(
                "asset/v1/content/assets",
                params={
                    "$page": 1,
                    "$pageSize": 50,
                    "$filter": "assetType.name=htmlemail",
                },
            )
            for raw in data.get("items", []):
                views = raw.get("views", {})
                html_view = views.get("html", {})

                template = EmailTemplate(
                    id=str(uuid4()),
                    name=raw.get("name", ""),
                    subject=raw.get("subject", {}).get("content"),
                    html_body=html_view.get("content"),
                    from_name=raw.get("fromName"),
                    from_email=raw.get("fromAddress"),
                    tags=raw.get("tags", []),
                    source_id=str(raw.get("id")),
                    source_platform="salesforce_marketing_cloud",
                    created_at=_parse_datetime(raw.get("createdDate")),
                    updated_at=_parse_datetime(raw.get("modifiedDate")),
                )
                templates.append(template)
        except requests.RequestException:
            logger.warning("Could not fetch templates from SFMC")

        logger.info(f"Fetched {len(templates)} templates from SFMC")
        return templates

    def fetch_events(self, contact_id: str | None = None) -> list[CustomEvent]:
        events = []

        if not contact_id:
            logger.info("SFMC event fetching requires a contact_id")
            return events

        try:
            data = self._get(
                "data/v1/customobjectdata/key/TrackingEvents/rowset",
                params={
                    "$filter": f"SubscriberKey eq '{contact_id}'",
                    "$page": 1,
                    "$pageSize": 100,
                },
            )
            for raw in data.get("items", []):
                values = raw.get("values", {})
                events.append(CustomEvent(
                    external_id=contact_id,
                    name=values.get("EventType", "unknown_event"),
                    time=_parse_datetime(values.get("EventDate")) or datetime.now(),
                    properties={
                        k: v for k, v in values.items()
                        if k not in ("SubscriberKey", "EventType", "EventDate")
                    },
                    source_id=values.get("EventId"),
                    source_platform="salesforce_marketing_cloud",
                ))
        except requests.RequestException:
            logger.warning(f"Could not fetch events for contact {contact_id}")

        logger.info(f"Fetched {len(events)} events from SFMC")
        return events


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
