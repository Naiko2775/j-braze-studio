from __future__ import annotations

import re

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base_mapper import BaseMapper


class DemoMapper(BaseMapper):
    """Mapper pour les donnees de demonstration."""

    def transform_contact(self, contact: Contact) -> Contact:
        transformed_attrs = []
        for attr in contact.custom_attributes:
            new_key = self._remap_attribute_key(attr.key)
            transformed_attrs.append(
                ContactAttribute(key=new_key, value=attr.value, type=attr.type)
            )
        return contact.model_copy(update={"custom_attributes": transformed_attrs})

    def transform_segment(self, segment: Segment) -> Segment:
        name = re.sub(r"[^\w\s-]", "", segment.name)
        name = re.sub(r"\s+", "_", name).lower()
        return segment.model_copy(update={"name": name})

    def transform_template(self, template: EmailTemplate) -> EmailTemplate:
        html = template.html_body
        if html:
            # Convertir les variables demo {{ contact.ATTR }} en Liquid Braze
            html = re.sub(
                r"\{\{\s*contact\.(\w+)\s*\}\}",
                lambda m: _demo_var_to_liquid(m.group(1)),
                html,
            )
        return template.model_copy(update={"html_body": html})

    def transform_event(self, event: CustomEvent) -> CustomEvent:
        return event.model_copy(update={"name": f"demo_{event.name}"})


def _demo_var_to_liquid(attr: str) -> str:
    mapping = {
        "FIRSTNAME": "{{${first_name}}}",
        "LASTNAME": "{{${last_name}}}",
        "EMAIL": "{{${email_address}}}",
    }
    if attr.upper() in mapping:
        return mapping[attr.upper()]
    return "{{custom_attribute.${" + attr.lower() + "}}}"
