"""Connecteur CSV pour import depuis fichier plat."""
from __future__ import annotations

import csv
import io
import logging
from typing import Any
from uuid import uuid4

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base import BaseConnector

logger = logging.getLogger(__name__)


class CsvConnector(BaseConnector):
    """Connecteur generique pour fichiers CSV/fichiers plats."""

    @property
    def platform_name(self) -> str:
        return "csv"

    def _validate_config(self) -> None:
        if "csv_data" not in self.config and "csv_path" not in self.config:
            raise ValueError("CSV connector requires 'csv_data' (string) or 'csv_path' in config")

    def test_connection(self) -> bool:
        try:
            data = self._get_csv_data()
            reader = csv.DictReader(io.StringIO(data))
            headers = reader.fieldnames
            return headers is not None and len(headers) > 0
        except Exception:
            return False

    def _get_csv_data(self) -> str:
        if "csv_data" in self.config:
            return self.config["csv_data"]
        with open(self.config["csv_path"], "r", encoding=self.config.get("encoding", "utf-8")) as f:
            return f.read()

    def fetch_contacts(self, limit: int | None = None, offset: int = 0) -> list[Contact]:
        data = self._get_csv_data()
        delimiter = self.config.get("delimiter", ",")
        reader = csv.DictReader(io.StringIO(data), delimiter=delimiter)
        contacts = []

        field_mapping = self.config.get("field_mapping", {})
        # Default mapping: essayer de deviner les colonnes standard
        email_col = field_mapping.get("email", "email")
        first_name_col = field_mapping.get("first_name", "first_name")
        last_name_col = field_mapping.get("last_name", "last_name")
        phone_col = field_mapping.get("phone", "phone")
        id_col = field_mapping.get("external_id", "id")

        for i, row in enumerate(reader):
            if i < offset:
                continue
            if limit and len(contacts) >= limit:
                break

            external_id = row.get(id_col, str(uuid4()))
            custom_attrs = []
            standard_cols = {email_col, first_name_col, last_name_col, phone_col, id_col}

            for key, value in row.items():
                if key not in standard_cols and value:
                    custom_attrs.append(ContactAttribute(
                        key=key.lower().replace(" ", "_"),
                        value=value,
                        type="string",
                    ))

            contacts.append(Contact(
                external_id=str(external_id),
                email=row.get(email_col),
                first_name=row.get(first_name_col),
                last_name=row.get(last_name_col),
                phone=row.get(phone_col),
                custom_attributes=custom_attrs,
                source_id=str(external_id),
                source_platform="csv",
            ))

        logger.info(f"Parsed {len(contacts)} contacts from CSV")
        return contacts

    def fetch_segments(self) -> list[Segment]:
        return []

    def fetch_templates(self) -> list[EmailTemplate]:
        return []

    def fetch_events(self, contact_id: str | None = None) -> list[CustomEvent]:
        return []
