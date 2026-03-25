from __future__ import annotations

from abc import ABC, abstractmethod

from services.migration.models import Contact, CustomEvent, Segment, EmailTemplate


class BaseMapper(ABC):
    """Interface pour les mappers qui transforment les donnees source en modele normalise.

    Les connecteurs retournent deja des modeles normalises, mais les mappers
    permettent d'appliquer des transformations supplementaires (renommage d'attributs,
    filtrage, enrichissement) selon les besoins specifiques de chaque migration.
    """

    def __init__(self, field_mapping: dict[str, str] | None = None):
        self.field_mapping = field_mapping or {}

    @abstractmethod
    def transform_contact(self, contact: Contact) -> Contact:
        """Applique les transformations specifiques sur un contact."""

    @abstractmethod
    def transform_segment(self, segment: Segment) -> Segment:
        """Applique les transformations specifiques sur un segment."""

    @abstractmethod
    def transform_template(self, template: EmailTemplate) -> EmailTemplate:
        """Applique les transformations specifiques sur un template."""

    @abstractmethod
    def transform_event(self, event: CustomEvent) -> CustomEvent:
        """Applique les transformations specifiques sur un evenement."""

    def transform_contacts(self, contacts: list[Contact]) -> list[Contact]:
        return [self.transform_contact(c) for c in contacts]

    def transform_segments(self, segments: list[Segment]) -> list[Segment]:
        return [self.transform_segment(s) for s in segments]

    def transform_templates(self, templates: list[EmailTemplate]) -> list[EmailTemplate]:
        return [self.transform_template(t) for t in templates]

    def transform_events(self, events: list[CustomEvent]) -> list[CustomEvent]:
        return [self.transform_event(e) for e in events]

    def _remap_attribute_key(self, key: str) -> str:
        return self.field_mapping.get(key, key)
