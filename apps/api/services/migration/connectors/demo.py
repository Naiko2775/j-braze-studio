from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from services.migration.models import Contact, ContactAttribute, CustomEvent, Segment, EmailTemplate
from .base import BaseConnector

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "Gabriel", "Hannah",
    "Ivan", "Julia", "Kevin", "Laura", "Marc", "Nadia", "Olivier", "Pauline",
    "Quentin", "Rachel", "Simon", "Tatiana", "Ugo", "Valerie", "William", "Xena",
    "Yann", "Zoe", "Antoine", "Beatrice", "Cedric", "Delphine", "Emile", "Francoise",
    "Guillaume", "Helene", "Isabelle", "Jacques", "Karim", "Louise", "Mathieu", "Nathalie",
]

LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David",
    "Bertrand", "Roux", "Vincent", "Fournier", "Morel", "Girard", "Andre", "Mercier",
    "Blanc", "Guerin", "Boyer", "Garnier", "Chevalier", "Francois", "Legrand", "Muller",
]

COUNTRIES = ["France", "Belgium", "Switzerland", "Canada", "Luxembourg", "Monaco"]
CITIES = {
    "France": ["Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Toulouse", "Nantes", "Strasbourg"],
    "Belgium": ["Bruxelles", "Anvers", "Gand", "Liege"],
    "Switzerland": ["Geneve", "Zurich", "Lausanne", "Berne"],
    "Canada": ["Montreal", "Quebec", "Ottawa", "Toronto"],
    "Luxembourg": ["Luxembourg"],
    "Monaco": ["Monaco"],
}
LANGUAGES = ["fr", "en", "de", "nl", "it"]

SEGMENTS = [
    {"name": "Newsletter Hebdo", "desc": "Abonnes a la newsletter hebdomadaire"},
    {"name": "Clients VIP", "desc": "Clients avec plus de 5 achats"},
    {"name": "Prospects Chauds", "desc": "Leads ayant visite le site 3+ fois"},
    {"name": "Inactifs 90j", "desc": "Contacts sans activite depuis 90 jours"},
    {"name": "Black Friday 2025", "desc": "Segment cible pour le Black Friday"},
    {"name": "Programme Fidelite", "desc": "Membres du programme de fidelite"},
    {"name": "Panier Abandonne", "desc": "Contacts ayant abandonne leur panier"},
    {"name": "Early Adopters", "desc": "Premiers utilisateurs du produit"},
]

EVENT_TYPES = [
    "email_open", "email_click", "purchase", "page_view",
    "cart_add", "cart_abandon", "signup", "unsubscribe",
    "app_open", "product_view", "search", "form_submit",
]

DEMO_TEMPLATES = [
    {
        "name": "Welcome Email",
        "subject": "Bienvenue {{ contact.FIRSTNAME }} !",
        "html": "<html><body><h1>Bienvenue !</h1><p>Bonjour {{ contact.FIRSTNAME }}.</p></body></html>",
        "tags": ["onboarding", "welcome"],
    },
    {
        "name": "Promo Mensuelle",
        "subject": "{{ contact.FIRSTNAME }}, -20% ce mois-ci !",
        "html": "<html><body><h1>-20% sur tout le site</h1><p>Code : PROMO20</p></body></html>",
        "tags": ["promo", "mensuelle"],
    },
    {
        "name": "Relance Panier",
        "subject": "Vous avez oublie quelque chose, {{ contact.FIRSTNAME }}",
        "html": "<html><body><h2>Votre panier vous attend !</h2></body></html>",
        "tags": ["retargeting", "cart"],
    },
    {
        "name": "Newsletter Hebdo",
        "subject": "Les actus de la semaine pour {{ contact.FIRSTNAME }}",
        "html": "<html><body><h1>Newsletter #42</h1></body></html>",
        "tags": ["newsletter", "weekly"],
    },
    {
        "name": "Anniversaire",
        "subject": "Joyeux anniversaire {{ contact.FIRSTNAME }} !",
        "html": "<html><body><h1>Joyeux Anniversaire !</h1></body></html>",
        "tags": ["birthday", "loyalty"],
    },
]

DEMO_CONTACT_COUNT = 250


class DemoConnector(BaseConnector):
    """Connecteur de demonstration avec donnees fictives."""

    def __init__(self, config: dict[str, Any]):
        self._seed = config.get("seed", 42)
        self._contact_count = config.get("contact_count", DEMO_CONTACT_COUNT)
        self._rng = random.Random(self._seed)
        super().__init__(config)

    @property
    def platform_name(self) -> str:
        return "demo"

    def _validate_config(self) -> None:
        pass  # Pas de validation necessaire pour la demo

    def test_connection(self) -> bool:
        return True

    def _random_date(self, start_year: int = 2023, end_year: int = 2025) -> datetime:
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        delta = (end - start).days
        return start + timedelta(days=self._rng.randint(0, delta))

    def _random_dob(self) -> str:
        year = self._rng.randint(1960, 2005)
        month = self._rng.randint(1, 12)
        day = self._rng.randint(1, 28)
        return f"{year}-{month:02d}-{day:02d}"

    def fetch_contacts(self, limit: int | None = None, offset: int = 0) -> list[Contact]:
        self._rng = random.Random(self._seed)  # Reset pour reproductibilite
        count = min(limit or self._contact_count, self._contact_count)
        contacts = []

        segment_ids_pool = [str(i) for i in range(len(SEGMENTS))]

        for i in range(offset, offset + count):
            first = self._rng.choice(FIRST_NAMES)
            last = self._rng.choice(LAST_NAMES)
            country = self._rng.choice(COUNTRIES)
            city = self._rng.choice(CITIES[country])
            lang = self._rng.choice(LANGUAGES)

            # Attributs custom varies
            custom_attrs = []
            if self._rng.random() > 0.3:
                custom_attrs.append(ContactAttribute(
                    key="lifetime_value",
                    value=round(self._rng.uniform(0, 5000), 2),
                    type="number",
                ))
            if self._rng.random() > 0.4:
                custom_attrs.append(ContactAttribute(
                    key="acquisition_channel",
                    value=self._rng.choice(["organic", "paid_search", "social", "referral", "email", "direct"]),
                    type="string",
                ))
            if self._rng.random() > 0.5:
                custom_attrs.append(ContactAttribute(
                    key="loyalty_points",
                    value=self._rng.randint(0, 10000),
                    type="number",
                ))
            if self._rng.random() > 0.6:
                custom_attrs.append(ContactAttribute(
                    key="preferred_category",
                    value=self._rng.choice(["electronics", "fashion", "home", "sports", "beauty", "food"]),
                    type="string",
                ))
            if self._rng.random() > 0.7:
                custom_attrs.append(ContactAttribute(
                    key="is_premium",
                    value=self._rng.choice([True, False]),
                    type="boolean",
                ))
            if self._rng.random() > 0.5:
                custom_attrs.append(ContactAttribute(
                    key="last_purchase_date",
                    value=self._random_date(2024, 2025).strftime("%Y-%m-%d"),
                    type="date",
                ))

            # Statuts d'abonnement
            email_sub = self._rng.choices(
                ["subscribed", "opted_in", "unsubscribed"],
                weights=[70, 20, 10],
            )[0]

            # Segments aleatoires (1 a 3)
            nb_segments = self._rng.randint(1, 3)
            contact_segments = self._rng.sample(segment_ids_pool, min(nb_segments, len(segment_ids_pool)))

            contact = Contact(
                external_id=f"demo_{i:06d}",
                email=f"{first.lower()}.{last.lower()}{i}@example.com",
                phone=f"+33{self._rng.randint(600000000, 699999999)}",
                first_name=first,
                last_name=last,
                language=lang,
                country=country,
                city=city,
                gender=self._rng.choice(["M", "F", "O"]),
                date_of_birth=self._random_dob(),
                email_subscribe=email_sub,
                push_subscribe=self._rng.choice(["subscribed", "opted_in", "unsubscribed"]),
                custom_attributes=custom_attrs,
                segment_ids=contact_segments,
                created_at=self._random_date(2023, 2024),
                updated_at=self._random_date(2024, 2025),
                source_id=f"demo_{i:06d}",
                source_platform="demo",
            )
            contacts.append(contact)

        return contacts

    def fetch_segments(self) -> list[Segment]:
        self._rng = random.Random(self._seed + 100)
        segments = []

        all_contact_ids = [f"demo_{i:06d}" for i in range(self._contact_count)]

        for idx, seg_data in enumerate(SEGMENTS):
            seg_size = self._rng.randint(
                int(self._contact_count * 0.05),
                int(self._contact_count * 0.4),
            )
            members = self._rng.sample(all_contact_ids, min(seg_size, len(all_contact_ids)))

            segment = Segment(
                id=str(idx),
                name=seg_data["name"],
                description=seg_data["desc"],
                contact_ids=members,
                source_id=str(idx),
                source_platform="demo",
                created_at=self._random_date(2023, 2024),
                updated_at=self._random_date(2024, 2025),
            )
            segments.append(segment)

        return segments

    def fetch_templates(self) -> list[EmailTemplate]:
        templates = []

        for idx, tmpl_data in enumerate(DEMO_TEMPLATES):
            template = EmailTemplate(
                id=str(uuid4()),
                name=tmpl_data["name"],
                subject=tmpl_data["subject"],
                html_body=tmpl_data["html"],
                from_name="Mon Entreprise",
                from_email="contact@monentreprise.com",
                reply_to="support@monentreprise.com",
                tags=tmpl_data["tags"],
                source_id=f"tmpl_{idx}",
                source_platform="demo",
                created_at=datetime(2024, 1, 1) + timedelta(days=idx * 30),
                updated_at=datetime(2025, 1, 1) + timedelta(days=idx * 15),
            )
            templates.append(template)

        return templates

    def fetch_events(self, contact_id: str | None = None) -> list[CustomEvent]:
        self._rng = random.Random(self._seed + 200)
        events = []

        if contact_id:
            contact_ids = [contact_id]
        else:
            nb = min(50, self._contact_count)
            contact_ids = [f"demo_{i:06d}" for i in self._rng.sample(range(self._contact_count), nb)]

        for cid in contact_ids:
            nb_events = self._rng.randint(1, 8)
            for _ in range(nb_events):
                event = CustomEvent(
                    external_id=cid,
                    name=self._rng.choice(EVENT_TYPES),
                    time=self._random_date(2024, 2025),
                    properties={
                        "source": self._rng.choice(["web", "mobile", "email"]),
                        "value": round(self._rng.uniform(0, 200), 2) if self._rng.random() > 0.5 else None,
                        "campaign": f"campaign_{self._rng.randint(1, 20)}",
                    },
                    source_id=str(uuid4())[:8],
                    source_platform="demo",
                )
                events.append(event)

        return events
