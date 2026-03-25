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

BREVO_API_BASE = "https://api.brevo.com/v3"


class BrevoConnector(BaseConnector):

    @property
    def platform_name(self) -> str:
        return "brevo"

    def _validate_config(self) -> None:
        if "api_key" not in self.config:
            raise ValueError("Brevo connector requires 'api_key' in config")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "api-key": self.config["api_key"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{BREVO_API_BASE}/{endpoint}"
        response = requests.get(url, headers=self._headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> bool:
        try:
            self._get("account")
            return True
        except requests.RequestException:
            return False

    def fetch_contacts(self, limit: int | None = None, offset: int = 0) -> list[Contact]:
        contacts = []
        page_limit = min(limit or 50, 50)
        current_offset = offset

        while True:
            data = self._get("contacts", params={"limit": page_limit, "offset": current_offset})
            raw_contacts = data.get("contacts", [])

            if not raw_contacts:
                break

            for raw in raw_contacts:
                contact = self._parse_contact(raw)
                contacts.append(contact)

            current_offset += len(raw_contacts)

            if limit and len(contacts) >= limit:
                contacts = contacts[:limit]
                break

            if len(raw_contacts) < page_limit:
                break

        logger.info(f"Fetched {len(contacts)} contacts from Brevo")
        return contacts

    def _parse_contact(self, raw: dict[str, Any]) -> Contact:
        attributes = raw.get("attributes", {})
        custom_attrs = []

        standard_fields = {
            "FIRSTNAME", "LASTNAME", "SMS", "LANGUE", "COUNTRY", "CITY", "GENDER", "DOB",
        }

        for key, value in attributes.items():
            if key not in standard_fields and value is not None:
                attr_type = "string"
                if isinstance(value, bool):
                    attr_type = "boolean"
                elif isinstance(value, (int, float)):
                    attr_type = "number"
                custom_attrs.append(ContactAttribute(key=key.lower(), value=value, type=attr_type))

        # Determiner le statut d'abonnement email
        email_subscribe = "subscribed"
        if raw.get("emailBlacklisted"):
            email_subscribe = "unsubscribed"

        # CORRECTION: smsBlacklisted ne mappe plus vers push_subscribe.
        # On stocke l'info dans un custom_attribute interne _sms_opt_out
        # qui sera traite par l'exporter via /subscription/status/set.
        if raw.get("smsBlacklisted"):
            custom_attrs.append(ContactAttribute(
                key="_sms_opt_out", value=True, type="boolean"
            ))

        return Contact(
            external_id=str(raw.get("id", uuid4())),
            email=raw.get("email"),
            phone=attributes.get("SMS"),
            first_name=attributes.get("FIRSTNAME"),
            last_name=attributes.get("LASTNAME"),
            language=attributes.get("LANGUE"),
            country=attributes.get("COUNTRY"),
            city=attributes.get("CITY"),
            gender=attributes.get("GENDER"),
            date_of_birth=attributes.get("DOB"),
            email_subscribe=email_subscribe,
            push_subscribe="subscribed",  # CORRECTION: ne plus toucher push_subscribe via smsBlacklisted
            custom_attributes=custom_attrs,
            segment_ids=[str(lid) for lid in raw.get("listIds", [])],
            created_at=_parse_datetime(raw.get("createdAt")),
            updated_at=_parse_datetime(raw.get("modifiedAt")),
            source_id=str(raw.get("id")),
            source_platform="brevo",
        )

    def fetch_segments(self) -> list[Segment]:
        segments = []
        data = self._get("contacts/lists", params={"limit": 50, "offset": 0})

        for raw_list in data.get("lists", []):
            segment = Segment(
                id=str(raw_list["id"]),
                name=raw_list["name"],
                description=raw_list.get("folderId"),
                contact_ids=[],
                source_id=str(raw_list["id"]),
                source_platform="brevo",
                created_at=_parse_datetime(raw_list.get("createdAt")),
                updated_at=_parse_datetime(raw_list.get("modifiedAt")),
            )

            try:
                list_contacts = self._get(
                    f"contacts/lists/{raw_list['id']}/contacts",
                    params={"limit": 500, "offset": 0},
                )
                segment.contact_ids = [
                    str(c["id"]) for c in list_contacts.get("contacts", [])
                ]
            except requests.RequestException:
                logger.warning(f"Could not fetch contacts for list {raw_list['id']}")

            segments.append(segment)

        logger.info(f"Fetched {len(segments)} segments from Brevo")
        return segments

    def fetch_templates(self) -> list[EmailTemplate]:
        templates = []
        data = self._get("smtp/templates", params={"limit": 50, "offset": 0})

        for raw in data.get("templates", []):
            template = EmailTemplate(
                id=str(uuid4()),
                name=raw.get("name", ""),
                subject=raw.get("subject", ""),
                html_body=raw.get("htmlContent"),
                from_name=raw.get("sender", {}).get("name"),
                from_email=raw.get("sender", {}).get("email"),
                reply_to=raw.get("replyTo"),
                tags=raw.get("tags", []),
                source_id=str(raw.get("id")),
                source_platform="brevo",
                created_at=_parse_datetime(raw.get("createdAt")),
                updated_at=_parse_datetime(raw.get("modifiedAt")),
            )
            templates.append(template)

        logger.info(f"Fetched {len(templates)} templates from Brevo")
        return templates

    def fetch_events(self, contact_id: str | None = None) -> list[CustomEvent]:
        events = []

        if contact_id:
            try:
                data = self._get(f"contacts/{contact_id}/campaignStats")
                for campaign in data.get("messagesSent", []):
                    events.append(CustomEvent(
                        external_id=contact_id,
                        name="email_sent",
                        time=_parse_datetime(campaign.get("date")) or datetime.now(),
                        properties={"campaign_name": campaign.get("campaignName")},
                        source_id=str(campaign.get("campaignId")),
                        source_platform="brevo",
                    ))
            except requests.RequestException:
                logger.warning(f"Could not fetch events for contact {contact_id}")

        logger.info(f"Fetched {len(events)} events from Brevo")
        return events


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
