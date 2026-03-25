"""
Referentiel du data model Braze -- objets, entites, attributs et relations.
Porte depuis braze_data_model/braze_data_model.py avec ajout de Feature Flags,
Preference Center et Canvas Entry Properties.
"""

BRAZE_DATA_MODEL = {
    "User Profile": {
        "description": "Profil utilisateur central dans Braze, identifie par external_id ou braze_id",
        "category": "core",
        "attributes": {
            "external_id": "Identifiant externe unique de l'utilisateur",
            "braze_id": "Identifiant interne Braze",
            "email": "Adresse email",
            "phone": "Numero de telephone",
            "first_name": "Prenom",
            "last_name": "Nom",
            "gender": "Genre (male, female, other, not_applicable, prefer_not_to_say)",
            "dob": "Date de naissance (YYYY-MM-DD)",
            "country": "Pays (code ISO-3166-1 alpha-2)",
            "city": "Ville",
            "language": "Langue preferee (code ISO-639-1)",
            "time_zone": "Fuseau horaire (IANA)",
            "home_city": "Ville de residence",
            "email_subscribe": "Statut opt-in email (opted_in, subscribed, unsubscribed)",
            "push_subscribe": "Statut opt-in push (opted_in, subscribed, unsubscribed)",
            "created_at": "Date de creation du profil",
            "last_used_app_date": "Derniere utilisation de l'app",
            "total_revenue": "Revenu total genere par l'utilisateur",
            "purchase_count": "Nombre total d'achats",
            "user_aliases": "Identifiants alternatifs pour les utilisateurs anonymes (avant identification)",
        },
        "children": ["Custom Attributes", "Custom Events", "Purchases", "Devices", "Subscription Groups"],
    },
    "Custom Attributes": {
        "description": "Attributs personnalises definis par le client, stockes sur le profil utilisateur",
        "category": "user_data",
        "attributes": {
            "key": "Nom de l'attribut personnalise",
            "value": "Valeur (string, number, boolean, date, array)",
            "data_type": "Type de donnee (string, integer, float, boolean, date, array)",
        },
        "parent": "User Profile",
        "children": [],
        "examples": [
            "loyalty_tier (string)",
            "total_points (integer)",
            "favorite_categories (array)",
            "last_store_visit (date)",
            "is_premium (boolean)",
        ],
    },
    "Custom Events": {
        "description": "Evenements personnalises trackes pour un utilisateur, utilises pour la segmentation et le declenchement de campagnes",
        "category": "user_data",
        "attributes": {
            "name": "Nom de l'evenement",
            "time": "Horodatage de l'evenement (ISO 8601)",
            "properties": "Proprietes associees a l'evenement (objet JSON)",
            "count": "Nombre d'occurrences (incremental)",
            "first_date": "Date de premiere occurrence",
            "last_date": "Date de derniere occurrence",
        },
        "parent": "User Profile",
        "children": ["Event Properties"],
        "examples": [
            "added_to_cart",
            "completed_onboarding",
            "viewed_product",
            "searched",
            "shared_content",
        ],
    },
    "Event Properties": {
        "description": "Proprietes associees a un evenement personnalise, permettent un ciblage granulaire",
        "category": "user_data",
        "attributes": {
            "key": "Nom de la propriete",
            "value": "Valeur de la propriete (string, number, boolean, date)",
        },
        "parent": "Custom Events",
        "children": [],
        "examples": [
            "product_id (string)",
            "category (string)",
            "price (float)",
            "quantity (integer)",
        ],
    },
    "Purchases": {
        "description": "Evenements d'achat trackes, utilises pour le calcul du revenu et la segmentation",
        "category": "user_data",
        "attributes": {
            "product_id": "Identifiant du produit achete",
            "currency": "Devise (code ISO 4217, ex: EUR, USD)",
            "price": "Prix de l'achat",
            "quantity": "Quantite achetee",
            "time": "Horodatage de l'achat (ISO 8601)",
            "properties": "Proprietes additionnelles (objet JSON)",
            "first_purchase_date": "Date du premier achat",
            "last_purchase_date": "Date du dernier achat",
        },
        "parent": "User Profile",
        "children": ["Purchase Properties"],
    },
    "Purchase Properties": {
        "description": "Proprietes associees a un achat",
        "category": "user_data",
        "attributes": {
            "key": "Nom de la propriete",
            "value": "Valeur de la propriete",
        },
        "parent": "Purchases",
        "children": [],
        "examples": ["brand (string)", "color (string)", "size (string)", "discount_code (string)"],
    },
    "Devices": {
        "description": "Appareils associes a un utilisateur pour les notifications push",
        "category": "user_data",
        "attributes": {
            "device_id": "Identifiant unique de l'appareil",
            "platform": "Plateforme (ios, android, web, kindle)",
            "model": "Modele de l'appareil",
            "os_version": "Version du systeme d'exploitation",
            "app_version": "Version de l'application",
            "push_token": "Token push de l'appareil",
            "push_enabled": "Push active sur cet appareil (boolean)",
            "ad_tracking_enabled": "Suivi publicitaire active (boolean)",
            "foreground_push_enabled": "Push au premier plan active (boolean)",
        },
        "parent": "User Profile",
        "children": [],
    },
    "Subscription Groups": {
        "description": "Groupes d'abonnement auxquels l'utilisateur est inscrit (email, SMS, WhatsApp)",
        "category": "user_data",
        "attributes": {
            "subscription_group_id": "Identifiant du groupe d'abonnement",
            "status": "Statut (subscribed, unsubscribed)",
            "channel": "Canal (email, sms, whatsapp)",
        },
        "parent": "User Profile",
        "children": [],
    },
    "Campaign": {
        "description": "Campagne de messaging Braze (email, push, in-app, SMS, etc.)",
        "category": "messaging",
        "attributes": {
            "campaign_id": "Identifiant unique de la campagne",
            "campaign_name": "Nom de la campagne",
            "channel": "Canal (email, push, in_app_message, sms, content_card, webhook)",
            "tags": "Tags associes a la campagne",
            "schedule_type": "Type de planification (scheduled, action_based, api_triggered)",
            "status": "Statut (draft, scheduled, active, stopped, archived)",
            "created_at": "Date de creation",
            "updated_at": "Date de derniere mise a jour",
            "send_in_local_time": "Envoi selon le fuseau horaire local de l'utilisateur (boolean)",
            "intelligent_delivery": "Envoi au moment optimal pour chaque utilisateur (boolean)",
            "rate_limit": "Limite de frequence d'envoi",
            "frequency_cap": "Plafond de frequence pour eviter la sur-sollicitation",
        },
        "children": ["Message Variant", "Conversion Event", "In-App Message", "Webhook"],
    },
    "Canvas": {
        "description": "Canvas Braze -- parcours client multi-etapes avec logique de branchement",
        "category": "messaging",
        "attributes": {
            "canvas_id": "Identifiant unique du canvas",
            "canvas_name": "Nom du canvas",
            "schedule_type": "Type de planification (scheduled, action_based, api_triggered)",
            "status": "Statut (draft, active, stopped, archived)",
            "created_at": "Date de creation",
            "updated_at": "Date de derniere mise a jour",
            "tags": "Tags associes",
            "exception_events": "Evenements qui retirent un utilisateur du Canvas",
            "exit_criteria": "Criteres de sortie globaux du Canvas",
            "entry_schedule": "Planification de l'entree dans le Canvas (scheduled, action_based, api_triggered)",
        },
        "children": ["Canvas Step", "Canvas Variant", "Canvas Entry Properties", "Conversion Event"],
    },
    "Canvas Step": {
        "description": "Etape individuelle dans un Canvas (message, delai, decision split, etc.)",
        "category": "messaging",
        "attributes": {
            "step_id": "Identifiant unique de l'etape",
            "step_name": "Nom de l'etape",
            "step_type": "Type (message, delay, decision_split, audience_split, action_paths, experiment_paths)",
            "channel": "Canal du message (si etape message)",
            "next_steps": "Etapes suivantes",
        },
        "parent": "Canvas",
        "children": [],
    },
    "Canvas Variant": {
        "description": "Variante d'un Canvas pour les tests A/B",
        "category": "messaging",
        "attributes": {
            "variant_id": "Identifiant de la variante",
            "variant_name": "Nom de la variante",
            "percentage": "Pourcentage du trafic",
        },
        "parent": "Canvas",
        "children": [],
    },
    "Canvas Entry Properties": {
        "description": "Proprietes passees a l'entree d'un Canvas API-triggered, accessibles dans toutes les etapes via canvas_entry_properties",
        "category": "messaging",
        "attributes": {
            "key": "Nom de la propriete d'entree",
            "value": "Valeur de la propriete (string, number, boolean, object)",
            "usage": "Accessible via {{canvas_entry_properties.${key}}} dans les messages Liquid",
        },
        "parent": "Canvas",
        "children": [],
        "examples": [
            "order_id (string) -- ID de commande pour un Canvas transactionnel",
            "product_name (string) -- Nom du produit pour personnalisation",
            "discount_amount (number) -- Montant de la remise",
        ],
    },
    "Segment": {
        "description": "Segment d'utilisateurs base sur des criteres (attributs, evenements, achats, etc.)",
        "category": "segmentation",
        "attributes": {
            "segment_id": "Identifiant unique du segment",
            "segment_name": "Nom du segment",
            "filters": "Criteres de filtrage (attributs, evenements, achats, engagement, etc.)",
            "size": "Taille estimee du segment",
            "created_at": "Date de creation",
            "updated_at": "Date de derniere mise a jour",
        },
        "referenced_by": ["Campaign", "Canvas"],
        "children": ["Segment Filter"],
    },
    "Segment Filter": {
        "description": "Filtre individuel compose dans un segment",
        "category": "segmentation",
        "attributes": {
            "filter_type": "Type (custom_attribute, custom_event, purchase, session, email_engagement, push_engagement, etc.)",
            "attribute_or_event": "Attribut ou evenement cible",
            "operator": "Operateur (equals, not_equals, greater_than, less_than, contains, etc.)",
            "value": "Valeur de comparaison",
        },
        "parent": "Segment",
        "children": [],
    },
    "Message Variant": {
        "description": "Variante de message dans une campagne (pour les tests A/B)",
        "category": "messaging",
        "attributes": {
            "variant_id": "Identifiant de la variante",
            "variant_name": "Nom de la variante",
            "percentage": "Pourcentage du trafic",
            "content": "Contenu du message",
        },
        "parent": "Campaign",
        "children": [],
    },
    "Conversion Event": {
        "description": "Evenement de conversion pour mesurer l'efficacite d'une campagne ou canvas",
        "category": "analytics",
        "attributes": {
            "event_type": "Type (custom_event, purchase, session_start, upgrade)",
            "event_name": "Nom de l'evenement (si custom_event)",
            "deadline": "Delai de conversion en jours",
        },
        "parent": ["Campaign", "Canvas"],
        "children": [],
    },
    "In-App Message": {
        "description": "Messages affiches dans l'application mobile ou web",
        "category": "messaging",
        "parent": "Campaign",
        "children": [],
        "attributes": {
            "message_type": "Type d'affichage (slideup, modal, full, html)",
            "trigger_event": "Evenement declencheur de l'affichage",
            "display_limit": "Nombre max d'affichages par utilisateur",
            "priority": "Priorite d'affichage si plusieurs messages eligibles",
            "duration": "Duree d'affichage en secondes",
            "click_action": "Action au clic (deeplink, URL, close)",
            "dismiss_type": "Comportement de fermeture (auto, swipe, button)",
            "header": "Titre du message",
            "body": "Corps du message",
            "image_url": "URL de l'image",
            "buttons": "Configuration des boutons (texte, action, couleur)",
        },
    },
    "Content Card": {
        "description": "Cartes de contenu persistantes dans le flux utilisateur",
        "category": "messaging",
        "children": [],
        "attributes": {
            "card_type": "Type de carte (classic, captioned_image, banner)",
            "title": "Titre de la carte",
            "description": "Description de la carte",
            "image_url": "URL de l'image",
            "url": "URL de redirection au clic",
            "pinned": "Carte epinglee en haut du flux (true/false)",
            "dismissible": "Peut etre fermee par l'utilisateur (true/false)",
            "expiration": "Date d'expiration de la carte",
            "extras": "Paires cle-valeur additionnelles (JSON)",
            "created_at": "Date de creation",
        },
    },
    "Webhook": {
        "description": "Requete HTTP vers un systeme externe declenchee par une campagne ou un Canvas",
        "category": "messaging",
        "parent": "Campaign",
        "children": [],
        "attributes": {
            "url": "URL de destination du webhook",
            "http_method": "Methode HTTP (POST, PUT, DELETE, PATCH)",
            "request_headers": "En-tetes HTTP personnalises",
            "request_body": "Corps de la requete (JSON ou texte avec Liquid)",
            "content_type": "Type de contenu (application/json, etc.)",
            "retry_policy": "Politique de retry en cas d'echec",
        },
    },
    "Catalog": {
        "description": "Catalogue de donnees referencees (produits, articles, etc.) pour la personnalisation",
        "category": "content",
        "attributes": {
            "catalog_name": "Nom du catalogue",
            "catalog_id": "Identifiant du catalogue",
            "fields": "Schema des champs du catalogue",
            "items_count": "Nombre d'elements",
        },
        "children": ["Catalog Item"],
    },
    "Catalog Item": {
        "description": "Element individuel d'un catalogue",
        "category": "content",
        "attributes": {
            "item_id": "Identifiant unique de l'element",
            "fields": "Champs de l'element (selon le schema du catalogue)",
        },
        "parent": "Catalog",
        "children": [],
    },
    "Content Block": {
        "description": "Bloc de contenu reutilisable dans les messages (HTML, Liquid)",
        "category": "content",
        "attributes": {
            "content_block_id": "Identifiant unique",
            "name": "Nom du content block",
            "content": "Contenu (HTML/Liquid)",
            "tags": "Tags associes",
        },
        "children": [],
    },
    "Connected Content": {
        "description": "Appel API externe au moment de l'envoi pour personnaliser le contenu",
        "category": "content",
        "attributes": {
            "url": "URL de l'API externe",
            "method": "Methode HTTP (GET, POST)",
            "headers": "En-tetes HTTP",
            "body": "Corps de la requete (si POST)",
            "content_type": "Type de contenu",
            "cache_duration": "Duree de cache en minutes",
        },
        "children": [],
    },
    "Currents": {
        "description": "Export en temps reel des evenements Braze vers un data warehouse ou partenaire",
        "category": "data_export",
        "attributes": {
            "connector_type": "Type de connecteur (S3, GCS, Azure Blob, Snowflake, etc.)",
            "event_types": "Types d'evenements exportes",
            "format": "Format (JSON, Avro)",
        },
        "children": ["Currents Event"],
    },
    "Currents Event": {
        "description": "Evenement exporte via Currents",
        "category": "data_export",
        "attributes": {
            "event_type": "Type d'evenement (message_send, message_open, message_click, etc.)",
            "properties": "Proprietes de l'evenement",
            "timestamp": "Horodatage",
        },
        "parent": "Currents",
        "children": [],
        "event_categories": {
            "email": ["email_send", "email_delivery", "email_open", "email_click", "email_bounce", "email_soft_bounce", "email_spam", "email_unsubscribe"],
            "push": ["push_send", "push_open", "push_bounce", "push_foreground"],
            "in_app_message": ["iam_impression", "iam_click"],
            "sms": ["sms_send", "sms_delivery", "sms_rejection", "sms_inbound_receive", "sms_opt_in", "sms_opt_out"],
            "content_card": ["content_card_impression", "content_card_click", "content_card_dismiss"],
            "webhook": ["webhook_send"],
            "user": ["custom_event", "purchase", "session_start", "session_end", "location"],
        },
    },
    "Feature Flags": {
        "description": "Feature flags Braze pour activer/desactiver des fonctionnalites par segment d'utilisateurs sans deploiement",
        "category": "content",
        "attributes": {
            "feature_flag_id": "Identifiant unique du feature flag",
            "name": "Nom du feature flag",
            "description": "Description de la fonctionnalite",
            "enabled": "Actif globalement (boolean)",
            "properties": "Proprietes additionnelles du feature flag (JSON key-value)",
            "rollout_percentage": "Pourcentage de deploiement (0-100)",
            "filter_segments": "Segments cibles pour l'activation",
        },
        "children": [],
    },
    "Preference Center": {
        "description": "Centre de preferences permettant aux utilisateurs de gerer leurs abonnements et preferences de communication",
        "category": "user_data",
        "attributes": {
            "preference_center_id": "Identifiant unique du centre de preferences",
            "name": "Nom du centre de preferences",
            "url": "URL du centre de preferences (hebergee par Braze)",
            "subscription_groups": "Groupes d'abonnement affiches dans le centre",
            "custom_preferences": "Preferences personnalisees (frequence, canaux, categories de contenu)",
            "branding": "Configuration de la marque (logo, couleurs)",
        },
        "parent": "User Profile",
        "children": [],
    },
}


def get_data_model_prompt() -> str:
    """Genere un prompt textuel decrivant le data model Braze pour l'agent."""
    lines = ["# Braze Data Model Reference\n"]
    for entity_name, entity in BRAZE_DATA_MODEL.items():
        lines.append(f"## {entity_name}")
        lines.append(f"**Description**: {entity['description']}")
        lines.append(f"**Categorie**: {entity['category']}")
        if entity.get("parent"):
            parent = entity["parent"]
            if isinstance(parent, list):
                lines.append(f"**Parents**: {', '.join(parent)}")
            else:
                lines.append(f"**Parent**: {parent}")
        if entity.get("referenced_by"):
            lines.append(f"**Reference par**: {', '.join(entity['referenced_by'])}")
        if entity.get("children"):
            lines.append(f"**Enfants**: {', '.join(entity['children'])}")
        lines.append("**Attributs**:")
        for attr, desc in entity["attributes"].items():
            lines.append(f"  - `{attr}`: {desc}")
        if entity.get("examples"):
            lines.append(f"**Exemples**: {', '.join(entity['examples'])}")
        if entity.get("event_categories"):
            lines.append("**Categories d'evenements**:")
            for cat, events in entity["event_categories"].items():
                lines.append(f"  - {cat}: {', '.join(events)}")
        lines.append("")
    return "\n".join(lines)


def get_all_entity_names() -> list[str]:
    """Retourne la liste de tous les noms d'entites."""
    return list(BRAZE_DATA_MODEL.keys())


def get_entity(name: str) -> dict | None:
    """Retourne une entite par son nom."""
    return BRAZE_DATA_MODEL.get(name)


def get_entities_by_category(category: str) -> list[str]:
    """Retourne les noms d'entites pour une categorie donnee."""
    return [name for name, entity in BRAZE_DATA_MODEL.items() if entity.get("category") == category]


def build_hierarchy() -> dict:
    """Construit l'arbre hierarchique du data model."""
    roots = []
    for name, entity in BRAZE_DATA_MODEL.items():
        if not entity.get("parent"):
            roots.append(_build_tree(name))
    return {"Braze Data Model": roots}


def _build_tree(name: str) -> dict:
    """Construit recursivement un noeud de l'arbre."""
    entity = BRAZE_DATA_MODEL.get(name, {})
    children = entity.get("children", [])
    node = {"name": name, "description": entity.get("description", "")}
    if children:
        node["children"] = [_build_tree(child) for child in children]
    return node


def get_full_hierarchy_mermaid() -> str:
    """Genere un diagramme Mermaid du data model complet."""
    lines = ["graph TD"]
    node_ids = {}
    counter = 0

    for name, entity in BRAZE_DATA_MODEL.items():
        if name not in node_ids:
            node_ids[name] = f"N{counter}"
            counter += 1
        node_id = node_ids[name]
        label = name.replace(" ", "<br/>")
        lines.append(f'  {node_id}["{label}"]')

    for name, entity in BRAZE_DATA_MODEL.items():
        for child in entity.get("children", []):
            if child not in node_ids:
                node_ids[child] = f"N{counter}"
                counter += 1
            lines.append(f"  {node_ids[name]} --> {node_ids[child]}")

    categories = {
        "core": "#2196F3",
        "user_data": "#4CAF50",
        "messaging": "#FF9800",
        "segmentation": "#9C27B0",
        "analytics": "#F44336",
        "content": "#00BCD4",
        "data_export": "#795548",
    }
    for name, entity in BRAZE_DATA_MODEL.items():
        cat = entity.get("category", "")
        color = categories.get(cat, "#607D8B")
        lines.append(f"  style {node_ids[name]} fill:{color},color:white")

    return "\n".join(lines)
