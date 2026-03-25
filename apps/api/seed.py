"""Seed script -- insere des donnees de demo realistes en BDD."""

import uuid
from datetime import datetime, timezone, timedelta

from models.db import SessionLocal, engine, Base
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob
from models.app_config import AppConfig

# Ensure tables exist
Base.metadata.create_all(bind=engine)

NOW = datetime.now(timezone.utc)


def _id():
    return str(uuid.uuid4())


# ── Helpers for timestamps spread over the last 30 days ──────────────────

def _ago(days=0, hours=0):
    return NOW - timedelta(days=days, hours=hours)


# =========================================================================
# 1. ANALYSES
# =========================================================================

ANALYSES = [
    {
        "project_name": "Fnac",
        "use_case": "Programme de bienvenue multi-canal",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=12),
        "result": {
            "use_case_analysis": [
                {
                    "use_case": "Programme de bienvenue multi-canal",
                    "description": "Canvas multi-etapes declenche a la creation du profil. Email de bienvenue immediat, push J+1 avec offre decouverte, in-app J+3 avec guide d'utilisation. Decision Splits pour adapter le parcours selon l'engagement.",
                    "required_data": [
                        {
                            "entity": "User Profile",
                            "attributes": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe", "created_at", "language"],
                            "custom_fields": [
                                {"name": "onboarding_completed", "type": "boolean", "description": "Indique si l'utilisateur a termine le parcours d'onboarding"},
                                {"name": "signup_source", "type": "string", "description": "Source d'inscription (web, app_ios, app_android, store)"},
                                {"name": "welcome_offer_code", "type": "string", "description": "Code promo de bienvenue attribue"},
                                {"name": "fnac_plus_member", "type": "boolean", "description": "Membre du programme Fnac+"}
                            ],
                            "purpose": "Profil de base pour personnaliser les messages de bienvenue et verifier les opt-ins"
                        },
                        {
                            "entity": "Custom Events",
                            "attributes": ["name", "time", "properties"],
                            "custom_fields": [
                                {"name": "account_created", "type": "string", "description": "Evenement trigger pour le Canvas de bienvenue"},
                                {"name": "first_purchase", "type": "string", "description": "Premier achat realise"},
                                {"name": "app_first_open", "type": "string", "description": "Premiere ouverture de l'app mobile"}
                            ],
                            "purpose": "Declenchement du Canvas et suivi des etapes cles du parcours"
                        },
                        {
                            "entity": "Canvas",
                            "attributes": ["canvas_id", "canvas_name", "schedule_type", "status"],
                            "custom_fields": [],
                            "purpose": "Orchestration du parcours de bienvenue multi-etapes"
                        },
                        {
                            "entity": "Canvas Step",
                            "attributes": ["step_id", "step_name", "step_type", "channel"],
                            "custom_fields": [],
                            "purpose": "Etapes: email bienvenue, delai, decision split, push decouverte, in-app guide"
                        },
                        {
                            "entity": "Content Block",
                            "attributes": ["content_block_id", "name", "content"],
                            "custom_fields": [],
                            "purpose": "Header et footer reutilisables, bloc offre bienvenue"
                        }
                    ],
                    "segments": [
                        {
                            "name": "Nouveaux inscrits Fnac (J-0)",
                            "filters": ["created_at est dans les dernieres 24 heures", "email_subscribe est opted_in OU push_subscribe est opted_in"]
                        },
                        {
                            "name": "Inscrits sans premier achat (J+7)",
                            "filters": ["created_at est entre 1 et 7 jours", "first_purchase n'a jamais ete realise"]
                        }
                    ],
                    "messaging": {
                        "channels": ["email", "push", "in_app_message"],
                        "trigger_type": "action_based",
                        "trigger_details": "Declenche sur l'evenement 'account_created'. Email immediat, push J+1, in-app J+3. Decision Splits sur ouverture email et completion onboarding."
                    }
                }
            ],
            "data_hierarchy": [
                {
                    "entity": "User Profile",
                    "attributes_used": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe", "created_at", "language"],
                    "children": [
                        {"entity": "Custom Attributes", "attributes_used": ["onboarding_completed", "signup_source", "welcome_offer_code", "fnac_plus_member"], "children": []},
                        {"entity": "Custom Events", "attributes_used": ["account_created", "first_purchase", "app_first_open"], "children": []}
                    ]
                },
                {"entity": "Canvas", "attributes_used": ["canvas_id", "canvas_name", "schedule_type", "status"], "children": [
                    {"entity": "Canvas Step", "attributes_used": ["step_id", "step_name", "step_type", "channel"], "children": []}
                ]},
                {"entity": "Content Block", "attributes_used": ["content_block_id", "name", "content"], "children": []}
            ],
            "mermaid_diagram": "graph TD\n    UP[User Profile] --> CA[Custom Attributes]\n    UP --> CE[Custom Events]\n    CV[Canvas] --> CS[Canvas Step]\n    CB[Content Block]\n    CV -.->|cible| SEG[Segment]\n    CS -.->|utilise| CB\n    CA --- CA_LIST[\"onboarding_completed<br/>signup_source<br/>welcome_offer_code<br/>fnac_plus_member\"]\n    CE --- CE_LIST[\"account_created<br/>first_purchase<br/>app_first_open\"]\n    style UP fill:#2196F3,color:white\n    style CA fill:#4CAF50,color:white\n    style CE fill:#4CAF50,color:white\n    style CV fill:#FF9800,color:white\n    style CS fill:#FF9800,color:white\n    style CB fill:#00BCD4,color:white\n    style SEG fill:#9C27B0,color:white"
        },
    },
    {
        "project_name": "Decathlon",
        "use_case": "Relance panier abandonne e-commerce",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=9, hours=6),
        "result": {
            "use_case_analysis": [
                {
                    "use_case": "Relance panier abandonne e-commerce",
                    "description": "Canvas action-based declenche quand un utilisateur ajoute un produit au panier sans finaliser l'achat dans les 2 heures. Utilise les Catalogues Braze pour afficher les details produits sport et le Connected Content pour les recommandations. Sequence: email H+2, push H+24, SMS H+48.",
                    "required_data": [
                        {
                            "entity": "User Profile",
                            "attributes": ["external_id", "email", "phone", "first_name", "email_subscribe", "push_subscribe"],
                            "custom_fields": [
                                {"name": "cart_value", "type": "float", "description": "Valeur totale du panier en cours"},
                                {"name": "cart_item_count", "type": "integer", "description": "Nombre d'articles dans le panier"},
                                {"name": "preferred_sport", "type": "string", "description": "Sport favori du client"},
                                {"name": "store_id", "type": "string", "description": "Magasin de reference pour le retrait"}
                            ],
                            "purpose": "Identification de l'utilisateur et personnalisation des messages de relance"
                        },
                        {
                            "entity": "Custom Events",
                            "attributes": ["name", "time", "properties"],
                            "custom_fields": [
                                {"name": "added_to_cart", "type": "string", "description": "Produit ajoute au panier"},
                                {"name": "started_checkout", "type": "string", "description": "Debut du processus de paiement"}
                            ],
                            "purpose": "Tracking du cycle de vie du panier"
                        },
                        {
                            "entity": "Catalog",
                            "attributes": ["catalog_name", "catalog_id", "fields"],
                            "custom_fields": [],
                            "purpose": "Catalogue produits sport pour afficher les details dans les emails"
                        },
                        {
                            "entity": "Connected Content",
                            "attributes": ["url", "method", "headers", "cache_duration"],
                            "custom_fields": [],
                            "purpose": "API de recommandation produit pour alternatives dans l'email"
                        },
                        {
                            "entity": "Purchases",
                            "attributes": ["product_id", "currency", "price", "quantity", "time"],
                            "custom_fields": [],
                            "purpose": "Conversion event pour arreter le Canvas quand l'achat est finalise"
                        }
                    ],
                    "segments": [
                        {"name": "Abandonnistes panier sport", "filters": ["A realise 'added_to_cart' dans les dernieres 2h", "N'a PAS realise 'started_checkout' dans les dernieres 2h", "cart_value > 0"]},
                        {"name": "Exclusion - Acheteurs recents", "filters": ["A effectue un achat dans les dernieres 2 heures"]}
                    ],
                    "messaging": {
                        "channels": ["email", "push", "sms"],
                        "trigger_type": "action_based",
                        "trigger_details": "Canvas declenche sur 'added_to_cart'. Delay 2h, puis verification si achat realise. Email H+2, push H+24, SMS H+48."
                    }
                }
            ],
            "data_hierarchy": [
                {"entity": "User Profile", "attributes_used": ["external_id", "email", "phone", "first_name"], "children": [
                    {"entity": "Custom Attributes", "attributes_used": ["cart_value", "cart_item_count", "preferred_sport", "store_id"], "children": []},
                    {"entity": "Custom Events", "attributes_used": ["added_to_cart", "started_checkout"], "children": []},
                    {"entity": "Purchases", "attributes_used": ["product_id", "currency", "price", "quantity", "time"], "children": []}
                ]},
                {"entity": "Catalog", "attributes_used": ["catalog_name", "catalog_id", "fields"], "children": []},
                {"entity": "Connected Content", "attributes_used": ["url", "method", "headers"], "children": []}
            ],
            "mermaid_diagram": "graph TD\n    UP[User Profile] --> CA[Custom Attributes]\n    UP --> CE[Custom Events]\n    UP --> PU[Purchases]\n    CAT[Catalog] --> CI[Catalog Item]\n    CC[Connected Content]\n    CV[Canvas] --> CS[Canvas Step]\n    CS -.->|utilise| CAT\n    CS -.->|utilise| CC\n    style UP fill:#2196F3,color:white\n    style CA fill:#4CAF50,color:white\n    style CE fill:#4CAF50,color:white\n    style PU fill:#4CAF50,color:white\n    style CAT fill:#00BCD4,color:white\n    style CI fill:#00BCD4,color:white\n    style CC fill:#00BCD4,color:white\n    style CV fill:#FF9800,color:white\n    style CS fill:#FF9800,color:white"
        },
    },
    {
        "project_name": "Sephora",
        "use_case": "Programme de fidelite 3 niveaux",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=7, hours=3),
        "result": {
            "use_case_analysis": [
                {
                    "use_case": "Programme de fidelite 3 niveaux",
                    "description": "Systeme de fidelite Beauty Insider avec 3 paliers (White, Black, Gold). Chaque achat genere des points. Canvas action-based surveille les changements de palier et envoie des notifications de felicitations + avantages exclusifs. Recapitulatif mensuel par email.",
                    "required_data": [
                        {
                            "entity": "User Profile",
                            "attributes": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe", "total_revenue", "purchase_count"],
                            "custom_fields": [
                                {"name": "beauty_tier", "type": "string", "description": "Palier actuel: white, black, gold"},
                                {"name": "beauty_points", "type": "integer", "description": "Points de fidelite Beauty Insider"},
                                {"name": "points_to_next_tier", "type": "integer", "description": "Points restants pour le palier suivant"},
                                {"name": "favorite_brand", "type": "string", "description": "Marque preferee du client"},
                                {"name": "skin_type", "type": "string", "description": "Type de peau pour personnalisation"}
                            ],
                            "purpose": "Donnees de fidelite stockees sur le profil"
                        },
                        {
                            "entity": "Custom Events",
                            "attributes": ["name", "time", "properties"],
                            "custom_fields": [
                                {"name": "tier_changed", "type": "string", "description": "Changement de palier fidelite"},
                                {"name": "points_earned", "type": "string", "description": "Points gagnes lors d'un achat"},
                                {"name": "reward_redeemed", "type": "string", "description": "Recompense utilisee"}
                            ],
                            "purpose": "Evenements du programme fidelite"
                        },
                        {
                            "entity": "Segment",
                            "attributes": ["segment_id", "segment_name", "filters"],
                            "custom_fields": [],
                            "purpose": "Segments par palier pour ciblage"
                        },
                        {
                            "entity": "Content Block",
                            "attributes": ["content_block_id", "name", "content"],
                            "custom_fields": [],
                            "purpose": "Blocs reutilisables: carte fidelite, barre de progression"
                        }
                    ],
                    "segments": [
                        {"name": "Membres White", "filters": ["beauty_tier = 'white'", "beauty_points entre 0 et 499"]},
                        {"name": "Membres Black", "filters": ["beauty_tier = 'black'", "beauty_points entre 500 et 1999"]},
                        {"name": "Membres Gold", "filters": ["beauty_tier = 'gold'", "beauty_points >= 2000"]}
                    ],
                    "messaging": {
                        "channels": ["email", "push", "in_app_message"],
                        "trigger_type": "action_based",
                        "trigger_details": "Canvas 1: declenche sur 'tier_changed', felicitations + avantages. Canvas 2: schedule mensuel, recapitulatif points."
                    }
                }
            ],
            "data_hierarchy": [
                {"entity": "User Profile", "attributes_used": ["external_id", "email", "first_name", "last_name", "total_revenue", "purchase_count"], "children": [
                    {"entity": "Custom Attributes", "attributes_used": ["beauty_tier", "beauty_points", "points_to_next_tier", "favorite_brand", "skin_type"], "children": []},
                    {"entity": "Custom Events", "attributes_used": ["tier_changed", "points_earned", "reward_redeemed"], "children": []}
                ]},
                {"entity": "Segment", "attributes_used": ["segment_id", "segment_name", "filters"], "children": []},
                {"entity": "Content Block", "attributes_used": ["content_block_id", "name", "content"], "children": []}
            ],
            "mermaid_diagram": "graph TD\n    UP[User Profile] --> CA[Custom Attributes]\n    UP --> CE[Custom Events]\n    SEG[Segment] --> SF[Segment Filter]\n    CB[Content Block]\n    CV[Canvas] --> CS[Canvas Step]\n    CV -.->|cible| SEG\n    CS -.->|utilise| CB\n    style UP fill:#2196F3,color:white\n    style CA fill:#4CAF50,color:white\n    style CE fill:#4CAF50,color:white\n    style SEG fill:#9C27B0,color:white\n    style SF fill:#9C27B0,color:white\n    style CB fill:#00BCD4,color:white\n    style CV fill:#FF9800,color:white\n    style CS fill:#FF9800,color:white"
        },
    },
    {
        "project_name": "BNP Paribas",
        "use_case": "Campagne de reactivation clients inactifs",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=5),
        "result": {
            "use_case_analysis": [
                {
                    "use_case": "Campagne de reactivation clients inactifs",
                    "description": "Canvas schedule pour reengager les clients bancaires inactifs depuis 60+ jours. Sequence progressive: email informatif, push rappel avantages, email offre speciale. Respect strict du consentement RGPD et des heures d'envoi bancaires.",
                    "required_data": [
                        {
                            "entity": "User Profile",
                            "attributes": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe"],
                            "custom_fields": [
                                {"name": "last_app_login", "type": "date", "description": "Derniere connexion a l'app bancaire"},
                                {"name": "account_type", "type": "string", "description": "Type de compte: particulier, professionnel, premium"},
                                {"name": "relationship_manager", "type": "string", "description": "Nom du conseiller attribue"},
                                {"name": "products_held", "type": "array", "description": "Liste des produits bancaires detenus"},
                                {"name": "rgpd_consent_marketing", "type": "boolean", "description": "Consentement marketing RGPD"}
                            ],
                            "purpose": "Identification et segmentation des clients inactifs"
                        },
                        {
                            "entity": "Custom Events",
                            "attributes": ["name", "time", "properties"],
                            "custom_fields": [
                                {"name": "app_login", "type": "string", "description": "Connexion a l'application bancaire"},
                                {"name": "transaction_completed", "type": "string", "description": "Transaction bancaire realisee"},
                                {"name": "appointment_booked", "type": "string", "description": "Rendez-vous en agence pris"}
                            ],
                            "purpose": "Suivi de l'activite client et mesure de la reactivation"
                        },
                        {
                            "entity": "Segment",
                            "attributes": ["segment_id", "segment_name", "filters"],
                            "custom_fields": [],
                            "purpose": "Segments d'inactivite pour ciblage progressif"
                        },
                        {
                            "entity": "Conversion Event",
                            "attributes": ["event_type", "event_name", "deadline"],
                            "custom_fields": [],
                            "purpose": "Mesure: connexion app ou transaction dans les 14 jours"
                        }
                    ],
                    "segments": [
                        {"name": "Inactifs 60-90 jours", "filters": ["last_app_login entre 60 et 90 jours", "rgpd_consent_marketing est true"]},
                        {"name": "Inactifs 90+ jours (critiques)", "filters": ["last_app_login > 90 jours", "rgpd_consent_marketing est true"]},
                        {"name": "Clients reactives", "filters": ["A realise 'app_login' dans les 14 derniers jours", "Etait dans le segment inactifs"]}
                    ],
                    "messaging": {
                        "channels": ["email", "push"],
                        "trigger_type": "scheduled",
                        "trigger_details": "Canvas schedule hebdomadaire le lundi 10h. Email informatif J+0, push rappel J+3, email offre speciale J+7. Heures d'envoi limitees 9h-19h."
                    }
                }
            ],
            "data_hierarchy": [
                {"entity": "User Profile", "attributes_used": ["external_id", "email", "first_name", "last_name"], "children": [
                    {"entity": "Custom Attributes", "attributes_used": ["last_app_login", "account_type", "relationship_manager", "products_held", "rgpd_consent_marketing"], "children": []},
                    {"entity": "Custom Events", "attributes_used": ["app_login", "transaction_completed", "appointment_booked"], "children": []}
                ]},
                {"entity": "Segment", "attributes_used": ["segment_id", "segment_name", "filters"], "children": []},
                {"entity": "Conversion Event", "attributes_used": ["event_type", "event_name", "deadline"], "children": []}
            ],
            "mermaid_diagram": "graph TD\n    UP[User Profile] --> CA[Custom Attributes]\n    UP --> CE[Custom Events]\n    SEG[Segment] --> SF[Segment Filter]\n    CONV[Conversion Event]\n    CV[Canvas] --> CS[Canvas Step]\n    CV -.->|cible| SEG\n    CV -.->|mesure| CONV\n    style UP fill:#2196F3,color:white\n    style CA fill:#4CAF50,color:white\n    style CE fill:#4CAF50,color:white\n    style SEG fill:#9C27B0,color:white\n    style SF fill:#9C27B0,color:white\n    style CONV fill:#F44336,color:white\n    style CV fill:#FF9800,color:white\n    style CS fill:#FF9800,color:white"
        },
    },
    {
        "project_name": "Leroy Merlin",
        "use_case": "Notifications transactionnelles post-achat",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=2, hours=8),
        "result": {
            "use_case_analysis": [
                {
                    "use_case": "Notifications transactionnelles post-achat",
                    "description": "Canvas action-based declenche apres chaque achat en magasin ou en ligne. Envoie confirmation de commande, suivi de livraison, demande d'avis a J+7, et suggestions de produits complementaires a J+14. Utilise Connected Content pour le tracking transporteur.",
                    "required_data": [
                        {
                            "entity": "User Profile",
                            "attributes": ["external_id", "email", "first_name", "phone", "email_subscribe", "push_subscribe"],
                            "custom_fields": [
                                {"name": "preferred_store", "type": "string", "description": "Magasin de reference du client"},
                                {"name": "diy_level", "type": "string", "description": "Niveau bricolage: debutant, intermediaire, expert"},
                                {"name": "project_in_progress", "type": "string", "description": "Projet en cours (renovation cuisine, jardin, etc.)"}
                            ],
                            "purpose": "Profil client pour personnalisation des messages post-achat"
                        },
                        {
                            "entity": "Purchases",
                            "attributes": ["product_id", "currency", "price", "quantity", "time"],
                            "custom_fields": [],
                            "purpose": "Historique d'achats et declencheur du Canvas"
                        },
                        {
                            "entity": "Custom Events",
                            "attributes": ["name", "time", "properties"],
                            "custom_fields": [
                                {"name": "order_confirmed", "type": "string", "description": "Confirmation de commande"},
                                {"name": "order_shipped", "type": "string", "description": "Commande expediee"},
                                {"name": "order_delivered", "type": "string", "description": "Commande livree"},
                                {"name": "review_submitted", "type": "string", "description": "Avis client depose"}
                            ],
                            "purpose": "Suivi du cycle de vie de la commande"
                        },
                        {
                            "entity": "Catalog",
                            "attributes": ["catalog_name", "catalog_id", "fields"],
                            "custom_fields": [],
                            "purpose": "Catalogue produits pour affichage dans les emails et recommandations"
                        },
                        {
                            "entity": "Connected Content",
                            "attributes": ["url", "method", "headers", "cache_duration"],
                            "custom_fields": [],
                            "purpose": "API tracking transporteur pour statut livraison en temps reel"
                        }
                    ],
                    "segments": [
                        {"name": "Acheteurs recents (J-0 a J-1)", "filters": ["A effectue un achat dans les dernieres 24h"]},
                        {"name": "En attente de livraison", "filters": ["A realise 'order_shipped'", "N'a PAS realise 'order_delivered'"]},
                        {"name": "Sans avis depose (J+7)", "filters": ["A realise 'order_delivered' entre 7 et 14 jours", "N'a PAS realise 'review_submitted'"]}
                    ],
                    "messaging": {
                        "channels": ["email", "push", "sms"],
                        "trigger_type": "action_based",
                        "trigger_details": "Canvas declenche sur 'purchase'. Confirmation immediate, suivi livraison via Connected Content, demande avis J+7, cross-sell J+14."
                    }
                }
            ],
            "data_hierarchy": [
                {"entity": "User Profile", "attributes_used": ["external_id", "email", "first_name", "phone"], "children": [
                    {"entity": "Custom Attributes", "attributes_used": ["preferred_store", "diy_level", "project_in_progress"], "children": []},
                    {"entity": "Custom Events", "attributes_used": ["order_confirmed", "order_shipped", "order_delivered", "review_submitted"], "children": []},
                    {"entity": "Purchases", "attributes_used": ["product_id", "currency", "price", "quantity", "time"], "children": []}
                ]},
                {"entity": "Catalog", "attributes_used": ["catalog_name", "catalog_id", "fields"], "children": []},
                {"entity": "Connected Content", "attributes_used": ["url", "method", "headers", "cache_duration"], "children": []}
            ],
            "mermaid_diagram": "graph TD\n    UP[User Profile] --> CA[Custom Attributes]\n    UP --> CE[Custom Events]\n    UP --> PU[Purchases]\n    CAT[Catalog] --> CI[Catalog Item]\n    CC[Connected Content]\n    CV[Canvas] --> CS[Canvas Step]\n    CS -.->|utilise| CAT\n    CS -.->|utilise| CC\n    style UP fill:#2196F3,color:white\n    style CA fill:#4CAF50,color:white\n    style CE fill:#4CAF50,color:white\n    style PU fill:#4CAF50,color:white\n    style CAT fill:#00BCD4,color:white\n    style CI fill:#00BCD4,color:white\n    style CC fill:#00BCD4,color:white\n    style CV fill:#FF9800,color:white\n    style CS fill:#FF9800,color:white"
        },
    },
]


# =========================================================================
# 2. GENERATIONS
# =========================================================================

GENERATIONS = [
    {
        "project_name": "Fnac",
        "brief": "Banniere hero pour les soldes d'ete avec -50% sur une selection de produits tech et culture. Ton premium et urgent. Couleurs Fnac jaune/noir.",
        "template_type": "hero_banner",
        "channel": "email",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=11, hours=4),
        "result": {
            "template": "hero_banner",
            "params": {
                "headline": "Soldes d'ete -50% {{ ${first_name} | default: '' }}",
                "subheadline": "Selection premium tech & culture reservee a nos meilleurs clients",
                "cta_text": "Voir la selection",
                "cta_url": "https://www.fnac.com/soldes-ete",
                "cta_color": "#E1A100",
                "bg_color": "#2D2D2D",
                "text_color": "#FFFFFF",
                "image_url": "https://images.fnac.com/banners/soldes-ete-2026.jpg"
            },
            "liquid_code": '<div style="background:#2D2D2D;color:#FFFFFF;padding:48px 32px;text-align:center;border-radius:12px;font-family:Helvetica,Arial,sans-serif;">\n  <div style="font-size:14px;text-transform:uppercase;letter-spacing:2px;color:#E1A100;margin-bottom:8px;">Soldes d\'ete</div>\n  <h1 style="font-size:32px;font-weight:800;margin:0 0 12px;">-50% sur une selection premium</h1>\n  <p style="font-size:16px;opacity:0.85;max-width:480px;margin:0 auto 24px;">{{ ${first_name} | default: \'Cher client\' }}, decouvrez notre selection tech & culture a prix casses</p>\n  <a href="https://www.fnac.com/soldes-ete" style="display:inline-block;background:#E1A100;color:#2D2D2D;padding:14px 36px;border-radius:6px;font-weight:700;text-decoration:none;font-size:16px;">Voir la selection</a>\n  <p style="font-size:12px;opacity:0.5;margin-top:20px;">Offre valable jusqu\'au 31 juillet 2026</p>\n</div>',
            "personalization_notes": "Utilise ${first_name} avec fallback 'Cher client'. La banniere peut etre personnalisee avec ${city} pour afficher le magasin le plus proche.",
            "ab_variants": [
                {"variant": "A", "headline": "Soldes d'ete -50%", "rationale": "Message direct sur la remise, fort impact visuel"},
                {"variant": "B", "headline": "Votre selection VIP a -50%", "rationale": "Ton exclusif et personnalise pour les clients fideles"}
            ]
        },
    },
    {
        "project_name": "Sephora",
        "brief": "Product card pour la nouvelle collection automne/hiver, mise en avant du coffret 'Les Indispensables'. Prix 89EUR au lieu de 120EUR. Badge 'Nouveaute'. Ton elegant et feminin.",
        "template_type": "product_card",
        "channel": "email",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=8, hours=2),
        "result": {
            "template": "product_card",
            "params": {
                "product_name": "Coffret Les Indispensables",
                "price": "89,00 EUR",
                "old_price": "120,00 EUR",
                "badge": "Nouveaute",
                "headline": "Nouvelle collection automne/hiver",
                "cta_text": "Decouvrir le coffret",
                "cta_url": "https://www.sephora.fr/coffret-indispensables",
                "cta_color": "#000000",
                "bg_color": "#FFF5F5",
                "text_color": "#1A1A1A",
                "image_url": "https://images.sephora.fr/coffret-indispensables.jpg"
            },
            "liquid_code": '<div style="background:#FFF5F5;border-radius:16px;overflow:hidden;font-family:Georgia,serif;max-width:400px;margin:0 auto;">\n  <div style="background:#000;color:#fff;text-align:center;padding:6px;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Nouveaute</div>\n  <div style="padding:24px;text-align:center;">\n    <img src="https://images.sephora.fr/coffret-indispensables.jpg" alt="Coffret Les Indispensables" style="width:100%;max-width:300px;border-radius:8px;margin-bottom:16px;" />\n    <h2 style="font-size:20px;color:#1A1A1A;margin:0 0 8px;">Coffret Les Indispensables</h2>\n    <p style="font-size:14px;color:#666;margin:0 0 12px;">{{ ${first_name} | default: \'Belle\' }}, votre routine beaute complete</p>\n    <div style="margin:12px 0;">\n      <span style="font-size:24px;font-weight:700;color:#C41E3A;">89,00 EUR</span>\n      <span style="font-size:16px;text-decoration:line-through;color:#999;margin-left:8px;">120,00 EUR</span>\n    </div>\n    <a href="https://www.sephora.fr/coffret-indispensables" style="display:inline-block;background:#000;color:#fff;padding:12px 32px;border-radius:24px;text-decoration:none;font-weight:600;">Decouvrir le coffret</a>\n  </div>\n</div>',
            "personalization_notes": "Utilise ${first_name} avec fallback 'Belle' pour un ton feminin et personnalise.",
            "ab_variants": [
                {"variant": "A", "headline": "Nouvelle collection automne/hiver", "rationale": "Focus sur la nouveaute saisonniere"},
                {"variant": "B", "headline": "Votre coffret beaute a -26%", "rationale": "Focus sur le prix et la promotion"}
            ]
        },
    },
    {
        "project_name": "Decathlon",
        "brief": "Countdown pour une flash sale de 24h sur les equipements de running. Urgence maximale. Couleurs Decathlon bleu/blanc.",
        "template_type": "countdown",
        "channel": "in-app",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=6),
        "result": {
            "template": "countdown",
            "params": {
                "headline": "Flash Sale Running -40%",
                "subheadline": "24h seulement ! Chaussures, vetements, accessoires",
                "end_date": "2026-04-15T23:59:00Z",
                "cta_text": "J'en profite",
                "cta_url": "https://www.decathlon.fr/flash-sale-running",
                "cta_color": "#FFFFFF",
                "bg_color": "#0066CC",
                "text_color": "#FFFFFF"
            },
            "liquid_code": '<div style="background:linear-gradient(135deg,#0066CC 0%,#003D7A 100%);color:#FFFFFF;padding:40px 24px;text-align:center;border-radius:12px;font-family:Arial,sans-serif;">\n  <div style="font-size:12px;text-transform:uppercase;letter-spacing:3px;opacity:0.8;margin-bottom:8px;">Offre flash</div>\n  <h1 style="font-size:28px;font-weight:800;margin:0 0 8px;">Running -40%</h1>\n  <p style="font-size:15px;opacity:0.9;margin:0 0 20px;">{{ ${first_name} | default: \'Sportif\' }}, plus que quelques heures !</p>\n  <div style="display:flex;justify-content:center;gap:12px;margin:20px 0;">\n    <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:12px 16px;min-width:60px;"><div style="font-size:28px;font-weight:800;">{{ countdown_hours }}</div><div style="font-size:10px;text-transform:uppercase;">Heures</div></div>\n    <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:12px 16px;min-width:60px;"><div style="font-size:28px;font-weight:800;">{{ countdown_minutes }}</div><div style="font-size:10px;text-transform:uppercase;">Minutes</div></div>\n    <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:12px 16px;min-width:60px;"><div style="font-size:28px;font-weight:800;">{{ countdown_seconds }}</div><div style="font-size:10px;text-transform:uppercase;">Secondes</div></div>\n  </div>\n  <a href="https://www.decathlon.fr/flash-sale-running" style="display:inline-block;background:#FFFFFF;color:#0066CC;padding:14px 36px;border-radius:6px;font-weight:700;text-decoration:none;font-size:16px;">J\'en profite</a>\n</div>',
            "personalization_notes": "Utilise ${first_name} avec fallback 'Sportif'. Le countdown peut etre dynamique avec les variables Braze de countdown.",
            "ab_variants": [
                {"variant": "A", "headline": "Flash Sale Running -40%", "rationale": "Message direct avec le sport et la remise"},
                {"variant": "B", "headline": "Plus que 24h pour vos baskets", "rationale": "Ton conversationnel creant l'urgence"}
            ]
        },
    },
    {
        "project_name": "BNP Paribas",
        "brief": "CTA simple de bienvenue pour les nouveaux clients banque en ligne. Offre -15% sur les frais de tenue de compte la premiere annee. Ton professionnel et rassurant.",
        "template_type": "cta_simple",
        "channel": "email",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=4, hours=5),
        "result": {
            "template": "cta_simple",
            "params": {
                "headline": "Bienvenue {{ ${first_name} | default: '' }}, profitez de -15%",
                "cta_text": "Activer mon offre",
                "cta_url": "https://mabanque.bnpparibas/offre-bienvenue",
                "cta_color": "#00915A",
                "bg_color": "#FFFFFF",
                "text_color": "#1A1A1A"
            },
            "liquid_code": '<div style="background:#FFFFFF;border:1px solid #E5E5E5;padding:40px 32px;text-align:center;border-radius:8px;font-family:\'BNP Sans\',Helvetica,Arial,sans-serif;">\n  <div style="width:48px;height:48px;background:#00915A;border-radius:50%;margin:0 auto 16px;display:flex;align-items:center;justify-content:center;">\n    <span style="color:white;font-size:24px;">&#10003;</span>\n  </div>\n  <h1 style="font-size:24px;font-weight:700;color:#1A1A1A;margin:0 0 12px;">Bienvenue {{ ${first_name} | default: \'chez BNP Paribas\' }}</h1>\n  <p style="font-size:15px;color:#666;margin:0 0 24px;max-width:400px;margin-left:auto;margin-right:auto;">Profitez de -15% sur vos frais de tenue de compte pendant votre premiere annee.</p>\n  <a href="https://mabanque.bnpparibas/offre-bienvenue" style="display:inline-block;background:#00915A;color:#FFFFFF;padding:14px 40px;border-radius:4px;font-weight:600;text-decoration:none;font-size:16px;">Activer mon offre</a>\n  <p style="font-size:11px;color:#999;margin-top:16px;">Offre reservee aux nouveaux clients. Conditions sur bnpparibas.com</p>\n</div>',
            "personalization_notes": "Utilise ${first_name} avec fallback 'chez BNP Paribas' pour garder un ton professionnel meme sans prenom.",
            "ab_variants": [
                {"variant": "A", "headline": "Bienvenue, profitez de -15%", "rationale": "Direct et axe sur l'avantage financier"},
                {"variant": "B", "headline": "Votre banque vous souhaite la bienvenue", "rationale": "Ton institutionnel et chaleureux"}
            ]
        },
    },
    {
        "project_name": "Leroy Merlin",
        "brief": "Testimonial banniere avec un avis client sur un projet de renovation de cuisine. Social proof pour inciter a prendre rendez-vous en magasin. Ton inspirant.",
        "template_type": "testimonial",
        "channel": "content-card",
        "model_used": "claude-sonnet-4-20250514",
        "created_at": _ago(days=1, hours=6),
        "result": {
            "template": "testimonial",
            "params": {
                "quote": "Grace a Leroy Merlin, j'ai renove ma cuisine en 3 semaines. Le coach deco m'a aide a choisir les materiaux et le resultat est magnifique !",
                "author": "Marie D.",
                "role": "Cliente Leroy Merlin depuis 2019",
                "headline": "Nos clients temoignent",
                "cta_text": "Prendre rendez-vous",
                "cta_url": "https://www.leroymerlin.fr/rendez-vous-deco",
                "cta_color": "#78BE20",
                "bg_color": "#F5F5F0",
                "text_color": "#333333"
            },
            "liquid_code": '<div style="background:#F5F5F0;padding:40px 32px;border-radius:12px;font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">\n  <div style="text-align:center;margin-bottom:20px;">\n    <span style="font-size:48px;color:#78BE20;">&#10077;</span>\n  </div>\n  <p style="font-size:16px;color:#333;line-height:1.6;text-align:center;font-style:italic;margin:0 0 20px;">&laquo; Grace a Leroy Merlin, j\'ai renove ma cuisine en 3 semaines. Le coach deco m\'a aide a choisir les materiaux et le resultat est magnifique ! &raquo;</p>\n  <div style="text-align:center;margin-bottom:24px;">\n    <strong style="font-size:14px;color:#333;">Marie D.</strong><br/>\n    <span style="font-size:12px;color:#888;">Cliente Leroy Merlin depuis 2019</span>\n  </div>\n  <div style="text-align:center;">\n    <p style="font-size:14px;color:#666;margin:0 0 16px;">{{ ${first_name} | default: \'Cher client\' }}, et vous, quel est votre prochain projet ?</p>\n    <a href="https://www.leroymerlin.fr/rendez-vous-deco" style="display:inline-block;background:#78BE20;color:#FFFFFF;padding:12px 32px;border-radius:6px;font-weight:700;text-decoration:none;">Prendre rendez-vous</a>\n  </div>\n</div>',
            "personalization_notes": "Utilise ${first_name} avec fallback 'Cher client' pour interpeller le lecteur apres le temoignage.",
            "ab_variants": [
                {"variant": "A", "headline": "Nos clients temoignent", "rationale": "Social proof classique, mise en avant de la communaute"},
                {"variant": "B", "headline": "Ils ont renove avec nous", "rationale": "Ton plus concret axe sur le projet"}
            ]
        },
    },
]


# =========================================================================
# 3. MIGRATION JOBS
# =========================================================================

MIGRATION_JOBS = [
    {
        "platform": "brevo",
        "mode": "full",
        "config": {
            "source_config": {"api_key": "xkeysib-***REDACTED***"},
            "field_mapping": {
                "EMAIL": "email",
                "PRENOM": "first_name",
                "NOM": "last_name",
                "SMS": "phone",
                "DATE_INSCRIPTION": "signup_date",
                "LISTE_PRINCIPALE": "fnac_newsletter"
            },
            "contact_limit": 15000,
            "deduplicate_by_email": True
        },
        "status": "completed",
        "progress": {
            "stage": "completed",
            "total": 15000,
            "processed": 15000,
            "success": 14850,
            "failed": 150,
            "percent": 100
        },
        "result": {
            "total_contacts": 15000,
            "total_success": 14850,
            "total_failed": 150,
            "total_skipped_duplicates": 327,
            "duration_seconds": 482,
            "average_rate": "31.1 contacts/sec",
            "summary": "Migration Brevo -> Braze terminee. 14 850 contacts importes avec succes sur 15 000. 150 echecs (emails invalides). 327 doublons detectes et dedupliques."
        },
        "error_log": [
            {"type": "invalid_email", "count": 98, "sample": "format email invalide (ex: user@.com)"},
            {"type": "missing_external_id", "count": 37, "sample": "champ external_id manquant apres mapping"},
            {"type": "rate_limit", "count": 15, "sample": "429 Too Many Requests - retried successfully"}
        ],
        "started_at": _ago(days=14, hours=2),
        "completed_at": _ago(days=14, hours=1),
        "created_at": _ago(days=14, hours=3),
    },
    {
        "platform": "salesforce_mc",
        "mode": "full",
        "config": {
            "source_config": {"client_id": "***REDACTED***", "client_secret": "***REDACTED***", "subdomain": "mc-sephora"},
            "field_mapping": {
                "EmailAddress": "email",
                "FirstName": "first_name",
                "LastName": "last_name",
                "MobileNumber": "phone",
                "LoyaltyTier": "beauty_tier",
                "LoyaltyPoints": "beauty_points",
                "PreferredBrand": "favorite_brand"
            },
            "contact_limit": 50000,
            "deduplicate_by_email": True
        },
        "status": "completed",
        "progress": {
            "stage": "completed",
            "total": 50000,
            "processed": 50000,
            "success": 48750,
            "failed": 1250,
            "percent": 100
        },
        "result": {
            "total_contacts": 50000,
            "total_success": 48750,
            "total_failed": 1250,
            "total_skipped_duplicates": 1843,
            "duration_seconds": 1820,
            "average_rate": "27.5 contacts/sec",
            "summary": "Migration Salesforce MC -> Braze terminee avec erreurs partielles. 48 750 contacts importes sur 50 000. 1 250 echecs. 1 843 doublons dedupliques."
        },
        "error_log": [
            {"type": "invalid_email", "count": 420, "sample": "format email invalide ou domaine inexistant"},
            {"type": "missing_required_field", "count": 380, "sample": "champ EmailAddress vide dans la Data Extension"},
            {"type": "field_mapping_error", "count": 290, "sample": "champ LoyaltyTier contient des valeurs non attendues (ex: 'VIP' au lieu de 'gold')"},
            {"type": "rate_limit", "count": 85, "sample": "429 Braze rate limit - batch retried after backoff"},
            {"type": "payload_too_large", "count": 75, "sample": "custom attributes depassent la limite de 256 caracteres"}
        ],
        "started_at": _ago(days=10, hours=6),
        "completed_at": _ago(days=10, hours=5),
        "created_at": _ago(days=10, hours=7),
    },
    {
        "platform": "demo",
        "mode": "dry_run",
        "config": {
            "source_config": {"contact_count": 100},
            "field_mapping": None,
            "contact_limit": 100,
            "deduplicate_by_email": False
        },
        "status": "completed",
        "progress": {
            "stage": "completed",
            "total": 100,
            "processed": 100,
            "success": 100,
            "failed": 0,
            "percent": 100
        },
        "result": {
            "total_contacts": 100,
            "total_success": 100,
            "total_failed": 0,
            "total_skipped_duplicates": 0,
            "duration_seconds": 3,
            "average_rate": "33.3 contacts/sec",
            "dry_run": True,
            "summary": "Dry run termine avec succes. 100 contacts simules, aucune donnee envoyee a Braze. Mapping et validation OK."
        },
        "error_log": [],
        "started_at": _ago(days=6, hours=1),
        "completed_at": _ago(days=6, hours=1),
        "created_at": _ago(days=6, hours=1),
    },
    {
        "platform": "csv",
        "mode": "warmup",
        "config": {
            "source_config": {"file_path": "/uploads/bnp_contacts_export.csv", "delimiter": ";", "encoding": "utf-8"},
            "field_mapping": {
                "email_client": "email",
                "prenom": "first_name",
                "nom": "last_name",
                "telephone": "phone",
                "type_compte": "account_type",
                "date_ouverture": "account_opened_date",
                "conseiller": "relationship_manager"
            },
            "contact_limit": 5000,
            "deduplicate_by_email": True
        },
        "status": "completed",
        "progress": {
            "stage": "completed",
            "total": 5000,
            "processed": 5000,
            "success": 4950,
            "failed": 50,
            "percent": 100
        },
        "result": {
            "total_contacts": 5000,
            "total_success": 4950,
            "total_failed": 50,
            "stages": [
                {"stage_percent": 10, "contacts": 500, "success": 498, "failed": 2, "error_rate": 0.4, "status": "completed"},
                {"stage_percent": 25, "contacts": 1250, "success": 1240, "failed": 10, "error_rate": 0.8, "status": "completed"},
                {"stage_percent": 50, "contacts": 2500, "success": 2475, "failed": 25, "error_rate": 1.0, "status": "completed"},
                {"stage_percent": 100, "contacts": 5000, "success": 4950, "failed": 50, "error_rate": 1.0, "status": "completed"}
            ],
            "duration_seconds": 245,
            "average_rate": "20.4 contacts/sec",
            "summary": "Migration CSV en mode warmup completee. 4 etapes progressives (10%, 25%, 50%, 100%). Taux d'erreur stable a 1%. 4 950 contacts importes sur 5 000."
        },
        "error_log": [
            {"type": "invalid_phone", "count": 28, "sample": "numero de telephone au format non international (ex: 06.12.34.56.78)"},
            {"type": "invalid_email", "count": 15, "sample": "email invalide ou jetable detecte"},
            {"type": "encoding_error", "count": 7, "sample": "caracteres speciaux non UTF-8 dans le champ nom"}
        ],
        "started_at": _ago(days=3, hours=4),
        "completed_at": _ago(days=3, hours=3),
        "created_at": _ago(days=3, hours=5),
    },
]


# =========================================================================
# 4. APP CONFIG
# =========================================================================

APP_CONFIGS = [
    {"key": "default_model", "value": "claude-sonnet-4-20250514"},
    {"key": "braze_api_instance", "value": "EU-01"},
    {"key": "app_version", "value": "1.0.0"},
]


# =========================================================================
# EXECUTION
# =========================================================================

def seed():
    db = SessionLocal()
    try:
        # -- Analyses --
        for data in ANALYSES:
            a = Analysis(
                id=_id(),
                project_name=data["project_name"],
                use_case=data["use_case"],
                result=data["result"],
                model_used=data["model_used"],
                created_at=data["created_at"],
            )
            db.add(a)
        print(f"[OK] {len(ANALYSES)} analyses inserees")

        # -- Generations --
        for data in GENERATIONS:
            g = Generation(
                id=_id(),
                project_name=data["project_name"],
                brief=data["brief"],
                template_type=data["template_type"],
                channel=data["channel"],
                result=data["result"],
                model_used=data["model_used"],
                created_at=data["created_at"],
            )
            db.add(g)
        print(f"[OK] {len(GENERATIONS)} generations inserees")

        # -- Migration Jobs --
        for data in MIGRATION_JOBS:
            j = MigrationJob(
                id=_id(),
                platform=data["platform"],
                mode=data["mode"],
                config=data["config"],
                status=data["status"],
                progress=data["progress"],
                result=data["result"],
                error_log=data["error_log"],
                started_at=data["started_at"],
                completed_at=data["completed_at"],
                created_at=data["created_at"],
            )
            db.add(j)
        print(f"[OK] {len(MIGRATION_JOBS)} migration jobs inserees")

        # -- App Config (upsert) --
        for cfg in APP_CONFIGS:
            existing = db.query(AppConfig).filter(AppConfig.key == cfg["key"]).first()
            if existing:
                existing.value = cfg["value"]
            else:
                db.add(AppConfig(key=cfg["key"], value=cfg["value"]))
        print(f"[OK] {len(APP_CONFIGS)} app_config inserees")

        db.commit()
        print("\n=== Seed termine avec succes ===")
    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
