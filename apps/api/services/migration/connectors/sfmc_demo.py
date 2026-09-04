"""
Connecteur de demonstration Salesforce Marketing Cloud.

Sous-classe du vrai connecteur SFMC : seule la couche transport est remplacee
par des fixtures en memoire. Tout le reste (pagination, parsing des contacts,
regle Status -> unsubscribed, separation champs standards / champs custom) est
le code de production, donc la demo montre le comportement reel de l'outil.

Les donnees sont FICTIVES (aucune personne reelle, adresses en @example.com) et
generees avec une graine fixe pour etre reproductibles d'une demo a l'autre.
"""
from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from typing import Any

from .salesforce_mc import SalesforceMarketingCloudConnector

# Graine fixe : le jeu de donnees est identique a chaque execution
FIXTURE_SEED = 20250903
CONTACT_COUNT = 420
# Quelques doublons d'email volontaires pour rendre la deduplication visible
DUPLICATE_COUNT = 12

FIRST_NAMES = [
    "Amelie", "Baptiste", "Camille", "Damien", "Elodie", "Fabien", "Gaelle",
    "Hugo", "Ines", "Julien", "Karine", "Ludovic", "Manon", "Nicolas",
    "Ophelie", "Pierre-Yves", "Quentin", "Romane", "Sebastien", "Tiphaine",
    "Ulysse", "Violette", "Wilfried", "Xavier", "Yasmine", "Zacharie",
    "Anais", "Benoit", "Clarisse", "Dorian", "Eugenie", "Florent",
]

LAST_NAMES = [
    "Aubry", "Boucher", "Cazenave", "Delaunay", "Escoffier", "Fontaine",
    "Gaillard", "Hebert", "Imbert", "Jourdan", "Kerneur", "Lacombe",
    "Massart", "Noailles", "Ollivier", "Poirier", "Quesnel", "Rambaud",
    "Sauvage", "Tessier", "Urbain", "Vasseur", "Weber", "Ybarra",
]

COUNTRIES = ["France", "Belgium", "Switzerland", "Luxembourg", "Spain"]
CITIES = {
    "France": ["Paris", "Marseille", "Lyon", "Bordeaux", "Lille", "Nantes", "Nice"],
    "Belgium": ["Bruxelles", "Anvers", "Liege"],
    "Switzerland": ["Geneve", "Lausanne", "Zurich"],
    "Luxembourg": ["Luxembourg"],
    "Spain": ["Madrid", "Barcelone"],
}
LANGUAGES = ["fr", "fr", "fr", "en", "nl", "es"]
GENDERS = ["M", "F", None]

# Univers fictif inspire d'un portefeuille de marques spiritueux
BRANDS = [
    "Anisette Cap Sud", "Vodka Boreale", "Rhum Isla Verde", "Whisky Glen Aran",
    "Champagne Fleur de Craie", "Gin Comptoir 9", "Liqueur Cafe Nocturne",
]
CATEGORIES = ["Aperitif", "Spiritueux Premium", "Champagne", "Cocktail", "Sans Alcool"]
LOYALTY_TIERS = ["Decouverte", "Argent", "Or", "Prestige"]
OUTLETS = ["E-boutique", "Grande distribution", "Caviste", "Bar partenaire", "Duty free"]
SOURCE_CHANNELS = ["Landing page", "Jeu concours", "Evenement", "Bar partenaire", "Import CRM"]
NEWSLETTER_FREQUENCIES = ["Hebdomadaire", "Mensuelle", "Temps forts"]

# Repartition realiste des statuts SFMC
STATUS_WEIGHTS = [
    ("Active", 82),
    ("Unsubscribed", 10),
    ("Held", 4),
    ("Bounced", 4),
]

LIST_DEFINITIONS = [
    (1001, "Club Prestige FR", "Membres Or et Prestige du club fidelite France"),
    (1002, "Newsletter Cocktails", "Abonnes a la newsletter recettes cocktails"),
    (1003, "Temps forts Champagne", "Cible campagnes fetes de fin d'annee"),
    (1004, "Inactifs 180 jours", "Aucune ouverture depuis 180 jours"),
    (1005, "Prospects Evenements", "Leads collectes en salon et bar partenaire"),
    (1006, "Opt-out global", "Contacts desabonnes, exclusion de tous les envois"),
]

# Templates SFMC avec AMPscript : la conversion vers Liquid Braze est faite
# par le mapper de production (SalesforceMarketingCloudMapper).
TEMPLATE_DEFINITIONS = [
    {
        "id": 7001,
        "name": "Bienvenue Club",
        "subject": "Bienvenue au club, %%FirstName%% !",
        "from_name": "Club Cap Sud",
        "from_email": "club@example.com",
        "tags": ["onboarding", "club"],
        "html": (
            "<html><body>"
            "<h1>Bonjour %%FirstName%% %%LastName%%,</h1>"
            "<p>Votre statut actuel : <strong>%%=v(@LoyaltyTier)=%%</strong>.</p>"
            "<p>Vous cumulez %%=v(@LoyaltyPoints)=%% points.</p>"
            "<p>Votre identifiant club : %%SubscriberKey%%</p>"
            "</body></html>"
        ),
    },
    {
        "id": 7002,
        "name": "Selection du mois",
        "subject": "%%FirstName%%, votre selection %%=v(@PreferredBrand)=%%",
        "from_name": "Maison Cap Sud",
        "from_email": "selection@example.com",
        "tags": ["crm", "recurrent"],
        "html": (
            "<html><body>"
            "<p>Bonjour %%FirstName%%,</p>"
            "<p>Parce que vous aimez %%=v(@PreferredBrand)=%%, voici notre selection "
            "pour la categorie %%=v(@PreferredCategory)=%%.</p>"
            "<a href=\"https://example.com/selection\">Decouvrir</a>"
            "</body></html>"
        ),
    },
    {
        "id": 7003,
        "name": "Relance panier",
        "subject": "Votre panier vous attend, %%FirstName%%",
        "from_name": "E-boutique Cap Sud",
        "from_email": "boutique@example.com",
        "tags": ["ecommerce", "relance"],
        "html": (
            "<html><body>"
            "<p>%%FirstName%%, il reste des articles dans votre panier.</p>"
            "<p>Points fidelite disponibles : %%=v(@LoyaltyPoints)=%%</p>"
            "</body></html>"
        ),
    },
    {
        "id": 7004,
        "name": "Invitation degustation",
        "subject": "Invitation degustation a %%=v(@City)=%%",
        "from_name": "Evenements Cap Sud",
        "from_email": "evenements@example.com",
        "tags": ["evenement"],
        "html": (
            "<html><body>"
            "<p>Cher %%FirstName%%,</p>"
            "<p>Nous vous invitons a une degustation privee reservee aux membres "
            "%%=v(@LoyaltyTier)=%%.</p>"
            "<p>Reponse a envoyer a %%EmailAddress%%.</p>"
            "</body></html>"
        ),
    },
    {
        "id": 7005,
        "name": "Fetes de fin d'annee",
        "subject": "%%FirstName%%, nos coffrets de fetes",
        "from_name": "Maison Cap Sud",
        "from_email": "fetes@example.com",
        "tags": ["temps-fort", "champagne"],
        "html": (
            "<html><body>"
            "<p>Bonjour %%FirstName%%,</p>"
            "<p>Coffrets Champagne Fleur de Craie, livraison offerte des 2 bouteilles.</p>"
            "<p>Votre boutique preferee : %%=v(@FavoriteOutlet)=%%</p>"
            "</body></html>"
        ),
    },
    {
        "id": 7006,
        "name": "Reactivation 180j",
        "subject": "On vous a manque, %%FirstName%% ?",
        "from_name": "Club Cap Sud",
        "from_email": "club@example.com",
        "tags": ["reactivation"],
        "html": (
            "<html><body>"
            "<p>%%FirstName%%, votre derniere commande date du "
            "%%=v(@LastPurchaseDate)=%%.</p>"
            "<p>Revenez profiter de votre statut %%=v(@LoyaltyTier)=%%.</p>"
            "</body></html>"
        ),
    },
]

EVENT_TYPES = ["EmailSend", "EmailOpen", "EmailClick", "EmailBounce", "EmailUnsubscribe"]

# Cache module : les fixtures sont construites une seule fois par process
_FIXTURES: dict[str, Any] | None = None


def _weighted_status(rng: random.Random) -> str:
    total = sum(weight for _, weight in STATUS_WEIGHTS)
    draw = rng.randint(1, total)
    cumulative = 0
    for status, weight in STATUS_WEIGHTS:
        cumulative += weight
        if draw <= cumulative:
            return status
    return "Active"


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def _build_fixtures() -> dict[str, Any]:
    """Genere le jeu de donnees fictif (graine fixe, donc reproductible)."""
    rng = random.Random(FIXTURE_SEED)
    # Date de reference figee : aucune dependance a l'horloge courante
    reference = datetime(2026, 1, 15, 9, 0, 0)

    subscribers: list[dict[str, Any]] = []
    loyalty_rows: list[dict[str, Any]] = []
    emails: list[str] = []

    for index in range(CONTACT_COUNT):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        country = rng.choice(COUNTRIES)
        city = rng.choice(CITIES[country])
        status = _weighted_status(rng)
        tier = rng.choice(LOYALTY_TIERS)
        points = rng.randint(0, 4800)
        subscriber_key = f"SFMC-{100000 + index}"

        slug_first = first.lower().replace("-", "")
        slug_last = last.lower()
        email = f"{slug_first}.{slug_last}{index}@example.com"

        # Doublons volontaires : meme email, SubscriberKey different
        if index >= CONTACT_COUNT - DUPLICATE_COUNT:
            email = emails[index % (CONTACT_COUNT - DUPLICATE_COUNT)]

        emails.append(email)

        created = reference - timedelta(days=rng.randint(120, 1400), hours=rng.randint(0, 23))
        modified = created + timedelta(days=rng.randint(1, 110), hours=rng.randint(0, 23))
        birth = datetime(rng.randint(1958, 2002), rng.randint(1, 12), rng.randint(1, 28))
        last_purchase = reference - timedelta(days=rng.randint(3, 540))

        values = {
            # Champs standards reconnus par _parse_contact
            "EmailAddress": email,
            "FirstName": first,
            "LastName": last,
            "Phone": f"+336{rng.randint(10000000, 99999999)}",
            "Country": country,
            "City": city,
            "Gender": rng.choice(GENDERS),
            "DateOfBirth": birth.strftime("%Y-%m-%d"),
            "Language": rng.choice(LANGUAGES),
            "Status": status,
            "CreatedDate": _iso(created),
            "ModifiedDate": _iso(modified),
            # Champs custom PascalCase : convertis en snake_case par le mapper
            "LoyaltyTier": tier,
            "LoyaltyPoints": points,
            "PreferredBrand": rng.choice(BRANDS),
            "PreferredCategory": rng.choice(CATEGORIES),
            "FavoriteOutlet": rng.choice(OUTLETS),
            "SourceChannel": rng.choice(SOURCE_CHANNELS),
            "NewsletterFrequency": rng.choice(NEWSLETTER_FREQUENCIES),
            "LastPurchaseDate": last_purchase.strftime("%Y-%m-%d"),
            "LifetimeValue": round(rng.uniform(0, 1850), 2),
            "OptInSms": rng.random() < 0.38,
        }

        subscribers.append({
            "keys": {"SubscriberKey": subscriber_key},
            "values": values,
        })

        if tier in ("Or", "Prestige") or rng.random() < 0.25:
            loyalty_rows.append({
                "keys": {"SubscriberKey": subscriber_key},
                "values": {
                    "SubscriberKey": subscriber_key,
                    "TierName": tier,
                    "PointsBalance": points,
                    "ClubName": "Club Cap Sud",
                    "EnrollmentDate": _iso(created + timedelta(days=2)),
                },
            })

    # Historique d'envois : quelques campagnes par contact
    send_history: list[dict[str, Any]] = []
    tracking_events: list[dict[str, Any]] = []
    job_id = 90000

    for row in subscribers:
        subscriber_key = row["keys"]["SubscriberKey"]
        status = row["values"]["Status"]
        sends = rng.randint(1, 6) if status == "Active" else rng.randint(0, 2)

        for _ in range(sends):
            job_id += 1
            template = rng.choice(TEMPLATE_DEFINITIONS)
            send_date = reference - timedelta(days=rng.randint(1, 300), hours=rng.randint(0, 23))
            opened = rng.random() < (0.42 if status == "Active" else 0.08)
            clicked = opened and rng.random() < 0.31
            bounced = status == "Bounced" and rng.random() < 0.5

            send_history.append({
                "keys": {"JobID": str(job_id), "SubscriberKey": subscriber_key},
                "values": {
                    "SubscriberKey": subscriber_key,
                    "JobID": str(job_id),
                    "EmailName": template["name"],
                    "SendDate": _iso(send_date),
                    "Opened": opened,
                    "Clicked": clicked,
                    "Bounced": bounced,
                },
            })

            tracking_events.append({
                "keys": {"EventId": f"EVT-{job_id}"},
                "values": {
                    "SubscriberKey": subscriber_key,
                    "EventType": "EmailSend",
                    "EventDate": _iso(send_date),
                    "EventId": f"EVT-{job_id}",
                    "EmailName": template["name"],
                },
            })
            if opened:
                tracking_events.append({
                    "keys": {"EventId": f"EVT-{job_id}-O"},
                    "values": {
                        "SubscriberKey": subscriber_key,
                        "EventType": "EmailOpen",
                        "EventDate": _iso(send_date + timedelta(hours=2)),
                        "EventId": f"EVT-{job_id}-O",
                        "EmailName": template["name"],
                    },
                })
            if clicked:
                tracking_events.append({
                    "keys": {"EventId": f"EVT-{job_id}-C"},
                    "values": {
                        "SubscriberKey": subscriber_key,
                        "EventType": "EmailClick",
                        "EventDate": _iso(send_date + timedelta(hours=3)),
                        "EventId": f"EVT-{job_id}-C",
                        "EmailName": template["name"],
                        "LinkUrl": "https://example.com/selection",
                    },
                })

    # Listes SFMC + abonnements
    lists: list[dict[str, Any]] = []
    subscriptions: dict[str, list[dict[str, Any]]] = {}
    for list_id, name, description in LIST_DEFINITIONS:
        created = reference - timedelta(days=rng.randint(200, 900))
        lists.append({
            "id": list_id,
            "name": name,
            "description": description,
            "createdDate": _iso(created),
            "modifiedDate": _iso(created + timedelta(days=rng.randint(5, 180))),
        })

        members = []
        for row in subscribers:
            values = row["values"]
            key = row["keys"]["SubscriberKey"]
            if list_id == 1001 and values["LoyaltyTier"] in ("Or", "Prestige"):
                members.append(key)
            elif list_id == 1002 and values["PreferredCategory"] == "Cocktail":
                members.append(key)
            elif list_id == 1003 and values["PreferredCategory"] == "Champagne":
                members.append(key)
            elif list_id == 1004 and values["Status"] == "Held":
                members.append(key)
            elif list_id == 1005 and values["SourceChannel"] in ("Evenement", "Bar partenaire"):
                members.append(key)
            elif list_id == 1006 and values["Status"] == "Unsubscribed":
                members.append(key)
        subscriptions[str(list_id)] = [{"subscriberKey": k} for k in members[:500]]

    # Assets email (htmlemail) au format attendu par fetch_templates
    assets = []
    for template in TEMPLATE_DEFINITIONS:
        created = reference - timedelta(days=rng.randint(30, 700))
        assets.append({
            "id": template["id"],
            "name": template["name"],
            "subject": {"content": template["subject"]},
            "fromName": template["from_name"],
            "fromAddress": template["from_email"],
            "tags": template["tags"],
            "views": {"html": {"content": template["html"]}},
            "createdDate": _iso(created),
            "modifiedDate": _iso(created + timedelta(days=rng.randint(1, 90))),
        })

    return {
        "data_extensions": {
            "Subscribers": subscribers,
            "Loyalty_Members": loyalty_rows,
            "Send_History": send_history,
            "TrackingEvents": tracking_events,
        },
        "lists": lists,
        "subscriptions": subscriptions,
        "assets": assets,
    }


def get_fixtures() -> dict[str, Any]:
    """Retourne les fixtures (construites une seule fois par process)."""
    global _FIXTURES
    if _FIXTURES is None:
        _FIXTURES = _build_fixtures()
    return _FIXTURES


def _paginate(items: list[dict[str, Any]], params: dict | None) -> dict[str, Any]:
    """Reproduit la pagination SFMC ($page / $pageSize).

    Indispensable : fetch_contacts boucle tant que la page renvoyee est pleine,
    une reponse constante ferait boucler l'appelant a l'infini.
    """
    params = params or {}
    page = _to_int(params.get("$page"), 1)
    page_size = _to_int(params.get("$pageSize"), 50)
    page = max(page, 1)
    page_size = max(1, min(page_size, 2500))

    start = (page - 1) * page_size
    chunk = items[start: start + page_size]
    return {
        "items": chunk,
        "count": len(items),
        "page": page,
        "pageSize": page_size,
    }


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _apply_subscriber_filter(items: list[dict[str, Any]], filter_expr: Any) -> list[dict[str, Any]]:
    """Gere le seul filtre utilise par le connecteur : SubscriberKey eq '...'."""
    if not filter_expr or not isinstance(filter_expr, str):
        return items
    match = re.search(r"SubscriberKey\s+eq\s+'([^']+)'", filter_expr)
    if not match:
        return items
    wanted = match.group(1)
    return [
        row for row in items
        if row.get("values", {}).get("SubscriberKey") == wanted
        or row.get("keys", {}).get("SubscriberKey") == wanted
    ]


class SfmcDemoConnector(SalesforceMarketingCloudConnector):
    """Connecteur SFMC de demonstration : memes traitements, transport simule.

    Seuls quatre membres sont surcharges (_validate_config, _authenticate,
    test_connection, _get). Tous les fetch_* du connecteur reel passent par
    _get, donc ils fonctionnent tels quels sur les fixtures.
    """

    def _validate_config(self) -> None:
        """Aucun identifiant requis : le jeu de demonstration est local."""
        return None

    def _authenticate(self) -> None:
        """Jeton factice : aucun appel reseau vers SFMC."""
        self._access_token = "demo-access-token"
        self._token_expiry = datetime.now() + timedelta(hours=1)

    def test_connection(self) -> bool:
        return True

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Sert les fixtures en fonction de l'endpoint SFMC demande."""
        fixtures = get_fixtures()

        if endpoint.startswith("data/v1/customobjectdata/key/") and endpoint.endswith("/rowset"):
            de_key = endpoint[len("data/v1/customobjectdata/key/"): -len("/rowset")]
            rows = fixtures["data_extensions"].get(de_key, [])
            rows = _apply_subscriber_filter(rows, (params or {}).get("$filter"))
            return _paginate(rows, params)

        if endpoint == "contacts/v1/contacts":
            # Fallback du connecteur reel quand la Data Extension est absente
            return _paginate(fixtures["data_extensions"]["Subscribers"], params)

        if endpoint == "contacts/v1/lists":
            return _paginate(fixtures["lists"], params)

        if endpoint.startswith("contacts/v1/lists/") and endpoint.endswith("/subscriptions"):
            list_id = endpoint[len("contacts/v1/lists/"): -len("/subscriptions")]
            return _paginate(fixtures["subscriptions"].get(list_id, []), params)

        if endpoint == "asset/v1/content/assets":
            return _paginate(fixtures["assets"], params)

        return {"items": [], "count": 0}

    def describe_source(self) -> dict[str, Any]:
        """Metadonnees affichees dans l'apercu (Data Extensions, volumetrie)."""
        fixtures = get_fixtures()
        des = fixtures["data_extensions"]
        return {
            "is_demo": True,
            "notice": (
                "Jeu de donnees fictif : aucune personne reelle, adresses en "
                "@example.com. Aucune ecriture n'est envoyee vers Braze."
            ),
            "data_extensions": [
                {"key": "Subscribers", "rows": len(des["Subscribers"]),
                 "description": "Master subscriber list"},
                {"key": "Loyalty_Members", "rows": len(des["Loyalty_Members"]),
                 "description": "Programme de fidelite (paliers et points)"},
                {"key": "Send_History", "rows": len(des["Send_History"]),
                 "description": "Historique des envois email"},
                {"key": "TrackingEvents", "rows": len(des["TrackingEvents"]),
                 "description": "Ouvertures, clics et bounces"},
            ],
        }
