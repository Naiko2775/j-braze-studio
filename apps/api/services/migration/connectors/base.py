from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.migration.models import Contact, CustomEvent, Segment, EmailTemplate


class BaseConnector(ABC):
    """Interface abstraite pour tous les connecteurs source."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._validate_config()

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Nom de la plateforme source."""

    @abstractmethod
    def _validate_config(self) -> None:
        """Valide que la configuration contient les cles necessaires."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Teste la connexion a l'API source."""

    @abstractmethod
    def fetch_contacts(self, limit: int | None = None, offset: int = 0) -> list[Contact]:
        """Recupere les contacts depuis la source."""

    @abstractmethod
    def fetch_segments(self) -> list[Segment]:
        """Recupere les segments/listes depuis la source."""

    @abstractmethod
    def fetch_templates(self) -> list[EmailTemplate]:
        """Recupere les templates d'email depuis la source."""

    @abstractmethod
    def fetch_events(self, contact_id: str | None = None) -> list[CustomEvent]:
        """Recupere les evenements custom depuis la source."""

    def fetch_all(self) -> dict[str, list]:
        """Recupere toutes les donnees depuis la source."""
        return {
            "contacts": self.fetch_contacts(),
            "segments": self.fetch_segments(),
            "templates": self.fetch_templates(),
            "events": self.fetch_events(),
        }
