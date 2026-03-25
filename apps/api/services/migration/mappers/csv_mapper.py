"""Mapper CSV -- passe-through avec renommage optionnel."""
from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base_mapper import BaseMapper


class CsvMapper(BaseMapper):
    def transform_contact(self, contact: Contact) -> Contact:
        transformed = []
        for attr in contact.custom_attributes:
            new_key = self._remap_attribute_key(attr.key)
            transformed.append(ContactAttribute(key=new_key, value=attr.value, type=attr.type))
        return contact.model_copy(update={"custom_attributes": transformed})

    def transform_segment(self, segment: Segment) -> Segment:
        return segment

    def transform_template(self, template: EmailTemplate) -> EmailTemplate:
        return template

    def transform_event(self, event: CustomEvent) -> CustomEvent:
        return event
