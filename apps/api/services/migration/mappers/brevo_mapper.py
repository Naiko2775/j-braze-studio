from __future__ import annotations

import re

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base_mapper import BaseMapper


class BrevoMapper(BaseMapper):
    """Mapper pour transformer les donnees Brevo vers le format Braze.

    CORRECTION: smsBlacklisted ne mappe plus vers push_subscribe.
    Le champ smsBlacklisted est traite dans le connecteur comme un custom_attribute
    interne _sms_opt_out, puis gere par l'exporter via l'endpoint
    /subscription/status/set pour les Subscription Groups SMS.
    """

    def transform_contact(self, contact: Contact) -> Contact:
        # Remapper les attributs custom selon le field_mapping
        transformed_attrs = []
        for attr in contact.custom_attributes:
            new_key = self._remap_attribute_key(attr.key)
            transformed_attrs.append(
                ContactAttribute(key=new_key, value=attr.value, type=attr.type)
            )

        # CORRECTION: push_subscribe n'est plus modifie par smsBlacklisted.
        # Le mapping SMS est gere via _sms_opt_out -> Subscription Group SMS.
        return contact.model_copy(update={"custom_attributes": transformed_attrs})

    def transform_segment(self, segment: Segment) -> Segment:
        # Normaliser le nom du segment pour Braze (snake_case)
        name = re.sub(r"[^\w\s-]", "", segment.name)
        name = re.sub(r"\s+", "_", name).lower()
        return segment.model_copy(update={"name": name})

    def transform_template(self, template: EmailTemplate) -> EmailTemplate:
        html = template.html_body
        if html:
            # Convertir les variables Brevo {{ contact.ATTR }} -> Liquid {{ custom_attribute.${attr} }}
            html = re.sub(
                r"\{\{\s*contact\.(\w+)\s*\}\}",
                lambda m: _brevo_var_to_liquid(m.group(1)),
                html,
            )
        return template.model_copy(update={"html_body": html})

    def transform_event(self, event: CustomEvent) -> CustomEvent:
        # Prefixer les noms d'evenements pour identifier la source
        return event.model_copy(update={"name": f"brevo_{event.name}"})


def _brevo_var_to_liquid(brevo_attr: str) -> str:
    """Convertit un nom d'attribut Brevo en variable Liquid Braze."""
    mapping = {
        "FIRSTNAME": "{{${first_name}}}",
        "LASTNAME": "{{${last_name}}}",
        "EMAIL": "{{${email_address}}}",
        "SMS": "{{${phone_number}}}",
    }
    if brevo_attr.upper() in mapping:
        return mapping[brevo_attr.upper()]
    return "{{custom_attribute.${" + brevo_attr.lower() + "}}}"
