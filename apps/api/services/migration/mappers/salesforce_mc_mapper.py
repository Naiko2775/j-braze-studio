from __future__ import annotations

import re

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base_mapper import BaseMapper


class SalesforceMarketingCloudMapper(BaseMapper):
    """Mapper pour transformer les donnees SFMC vers le format Braze."""

    def transform_contact(self, contact: Contact) -> Contact:
        transformed_attrs = []
        for attr in contact.custom_attributes:
            # Convertir PascalCase SFMC -> snake_case pour Braze
            new_key = self._remap_attribute_key(_pascal_to_snake(attr.key))
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
            # Convertir les AMPscript SFMC -> Liquid Braze
            # %%=v(@variable)=%% -> {{ custom_attribute.${variable} }}
            html = re.sub(
                r"%%=v\(@(\w+)\)=%%",
                lambda m: _ampscript_var_to_liquid(m.group(1)),
                html,
            )
            # %%FirstName%% -> {{ ${first_name} }}
            html = re.sub(
                r"%%(\w+)%%",
                lambda m: _sfmc_personalization_to_liquid(m.group(1)),
                html,
            )
        return template.model_copy(update={"html_body": html})

    def transform_event(self, event: CustomEvent) -> CustomEvent:
        # Normaliser le nom d'evenement
        name = _pascal_to_snake(event.name)
        return event.model_copy(update={"name": f"sfmc_{name}"})


def _pascal_to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def _ampscript_var_to_liquid(var_name: str) -> str:
    mapping = {
        "FirstName": "{{${first_name}}}",
        "LastName": "{{${last_name}}}",
        "EmailAddress": "{{${email_address}}}",
    }
    if var_name in mapping:
        return mapping[var_name]
    return "{{custom_attribute.${" + _pascal_to_snake(var_name) + "}}}"


def _sfmc_personalization_to_liquid(field: str) -> str:
    mapping = {
        "FirstName": "{{${first_name}}}",
        "LastName": "{{${last_name}}}",
        "EmailAddress": "{{${email_address}}}",
        "SubscriberKey": "{{${user_id}}}",
    }
    if field in mapping:
        return mapping[field]
    return "{{custom_attribute.${" + _pascal_to_snake(field) + "}}}"
