"""
BrazeExporter -- exporte les donnees normalisees vers Braze.
Porte depuis braze_migration/exporters/braze.py avec corrections :
1. Rate limit HTTP 429 avec Retry-After
2. Erreurs partielles /users/track
3. Deduplication par email
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

from services.migration.models import Contact, CustomEvent, EmailTemplate

logger = logging.getLogger(__name__)

BATCH_SIZE = 75


def deduplicate_contacts_by_email(contacts: list[Contact]) -> list[Contact]:
    """Deduplique les contacts par email, gardant le plus recent (updated_at)."""
    seen: dict[str, Contact] = {}
    for contact in contacts:
        if not contact.email:
            # Pas d'email = pas de deduplication possible, garder tel quel
            seen[contact.external_id] = contact
            continue
        existing = seen.get(contact.email)
        if existing is None:
            seen[contact.email] = contact
        else:
            # Garder le plus recent
            existing_date = existing.updated_at
            current_date = contact.updated_at
            if current_date and (not existing_date or current_date > existing_date):
                seen[contact.email] = contact
    return list(seen.values())


class BrazeExporter:
    """Exporte les donnees normalisees vers Braze via l'API REST."""

    def __init__(self, config: dict[str, Any]):
        self.api_key = config["api_key"]
        self.api_url = config.get("api_url", "https://rest.iad-01.braze.com")
        self.dry_run = config.get("dry_run", False)
        self.sms_subscription_group_id = config.get("sms_subscription_group_id")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict, max_retries: int = 5) -> dict:
        """POST avec gestion du rate limit HTTP 429 (Retry-After)."""
        if self.dry_run:
            logger.info(f"[DRY RUN] POST {endpoint} with {len(str(payload))} bytes")
            return {"message": "dry_run"}

        url = f"{self.api_url}/{endpoint}"

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self._headers, json=payload, timeout=60)

                # CORRECTION 1: Gestion HTTP 429 avec Retry-After
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Rate limited (429). Retry-After: {retry_after}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait = min(2 ** attempt, 30)
                    logger.warning(f"Request failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        return {"message": "max_retries_exceeded"}

    def test_connection(self) -> bool:
        try:
            url = f"{self.api_url}/email/hard_bounces"
            response = requests.get(
                url, headers=self._headers, params={"start_date": "2024-01-01"}, timeout=10
            )
            return response.status_code != 401
        except requests.RequestException:
            return False

    def export_contacts(self, contacts: list[Contact]) -> dict[str, Any]:
        """Exporte les contacts vers Braze via /users/track.
        CORRECTION 2: Parse les erreurs partielles par batch."""
        results: dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

        for i in range(0, len(contacts), BATCH_SIZE):
            batch = contacts[i: i + BATCH_SIZE]
            attributes = [self._contact_to_braze_attributes(c) for c in batch]

            try:
                response = self._post("users/track", {"attributes": attributes})

                if response.get("message") in ("success", "dry_run"):
                    # Verifier les erreurs partielles
                    errors = response.get("errors", [])
                    if errors:
                        results["failed"] += len(errors)
                        results["success"] += len(batch) - len(errors)
                        for err in errors:
                            results["errors"].append({
                                "batch_index": i,
                                "error": err,
                            })
                        logger.warning(f"Batch {i}: {len(errors)} partial errors")
                    else:
                        results["success"] += len(batch)
                else:
                    results["failed"] += len(batch)
                    logger.warning(f"Batch {i} failed: {response}")

            except requests.RequestException as e:
                results["failed"] += len(batch)
                results["errors"].append({
                    "batch_index": i,
                    "error": str(e),
                })
                logger.error(f"Failed to export batch {i}: {e}")

        logger.info(
            f"Exported contacts: {results['success']} success, {results['failed']} failed"
        )
        return results

    def _contact_to_braze_attributes(self, contact: Contact) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "external_id": contact.external_id,
            "email_subscribe": contact.email_subscribe,
            # CORRECTION 3: push_subscribe n'est plus affecte par smsBlacklisted
            "push_subscribe": contact.push_subscribe,
            "_update_existing_only": False,
        }

        if contact.email:
            attrs["email"] = contact.email
        if contact.phone:
            attrs["phone"] = contact.phone
        if contact.first_name:
            attrs["first_name"] = contact.first_name
        if contact.last_name:
            attrs["last_name"] = contact.last_name
        if contact.language:
            attrs["language"] = contact.language
        if contact.country:
            attrs["country"] = contact.country
        if contact.city:
            attrs["home_city"] = contact.city
        if contact.gender:
            attrs["gender"] = contact.gender
        if contact.date_of_birth:
            attrs["dob"] = contact.date_of_birth

        for custom_attr in contact.custom_attributes:
            # Filtrer le marker interne _sms_opt_out
            if custom_attr.key == "_sms_opt_out":
                continue
            attrs[custom_attr.key] = custom_attr.value

        if contact.source_platform:
            attrs["migration_source"] = contact.source_platform
        if contact.source_id:
            attrs["migration_source_id"] = contact.source_id

        return attrs

    def set_sms_subscription(self, contacts: list[Contact]) -> dict[str, int]:
        """CORRECTION SMS: Gere les opt-out SMS via Subscription Group
        au lieu de mapper sur push_subscribe."""
        if not self.sms_subscription_group_id:
            logger.info("No SMS subscription group configured, skipping")
            return {"success": 0, "skipped": 0}

        results = {"success": 0, "failed": 0}

        sms_optout_contacts = [
            c for c in contacts
            if any(a.key == "_sms_opt_out" and a.value for a in c.custom_attributes)
        ]

        for contact in sms_optout_contacts:
            try:
                self._post("subscription/status/set", {
                    "subscription_group_id": self.sms_subscription_group_id,
                    "subscription_state": "unsubscribed",
                    "external_id": [contact.external_id],
                })
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                logger.error(f"Failed to set SMS subscription for {contact.external_id}: {e}")

        return results

    def export_events(self, events: list[CustomEvent]) -> dict[str, int]:
        results = {"success": 0, "failed": 0}
        for i in range(0, len(events), BATCH_SIZE):
            batch = events[i: i + BATCH_SIZE]
            braze_events = [
                {
                    "external_id": e.external_id,
                    "name": e.name,
                    "time": e.time.isoformat(),
                    "properties": e.properties,
                }
                for e in batch
            ]
            try:
                response = self._post("users/track", {"events": braze_events})
                if response.get("message") in ("success", "dry_run"):
                    results["success"] += len(batch)
                else:
                    results["failed"] += len(batch)
            except requests.RequestException:
                results["failed"] += len(batch)
        return results

    def export_templates(self, templates: list[EmailTemplate]) -> dict[str, int]:
        results = {"success": 0, "failed": 0}
        for template in templates:
            payload = {
                "template_name": template.name,
                "subject": template.subject or "",
                "body": template.html_body or "",
                "plaintext_body": template.text_body or "",
                "tags": template.tags,
            }
            try:
                response = self._post("templates/email/create", payload)
                if response.get("message") in ("success", "dry_run"):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except requests.RequestException:
                results["failed"] += 1
        return results

    def export_all(
        self,
        contacts: list[Contact],
        events: list[CustomEvent],
        templates: list[EmailTemplate],
    ) -> dict[str, dict]:
        return {
            "contacts": self.export_contacts(contacts),
            "events": self.export_events(events),
            "templates": self.export_templates(templates),
        }
