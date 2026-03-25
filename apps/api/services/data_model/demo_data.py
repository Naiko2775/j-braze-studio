"""Donnees de demonstration pour le module Data Model."""

DEMO_USE_CASES = [
    "Campagne de bienvenue email + push pour les nouveaux inscrits",
    "Relance panier abandonne avec recommandation produit personnalisee",
    "Programme de fidelite avec notifications sur les paliers de points",
]

DEMO_RESULTS = {
    "use_case_analysis": [
        {
            "use_case": "Campagne de bienvenue email + push pour les nouveaux inscrits",
            "description": "Un Canvas multi-etapes declenche automatiquement a la creation du profil utilisateur. Le parcours envoie un email de bienvenue immediatement, suivi d'une notification push J+1 avec une offre de decouverte. Un Decision Split verifie si l'email a ete ouvert pour adapter le message push.",
            "required_data": [
                {
                    "entity": "User Profile",
                    "attributes": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe", "created_at", "language"],
                    "custom_fields": [
                        {
                            "name": "onboarding_completed",
                            "type": "boolean",
                            "description": "Indique si l'utilisateur a termine le parcours d'onboarding",
                            "update_frequency": "once"
                        },
                        {
                            "name": "signup_source",
                            "type": "string",
                            "description": "Source d'inscription (web, app_ios, app_android, referral)",
                            "update_frequency": "once"
                        },
                        {
                            "name": "welcome_offer_code",
                            "type": "string",
                            "description": "Code promo de bienvenue attribue a l'utilisateur",
                            "update_frequency": "once"
                        }
                    ],
                    "purpose": "Profil de base pour personnaliser les messages de bienvenue et verifier les opt-ins"
                },
                {
                    "entity": "Custom Events",
                    "attributes": ["name", "time", "properties"],
                    "custom_fields": [
                        {
                            "name": "account_created",
                            "type": "string",
                            "description": "Evenement declenche a la creation du compte, sert de trigger pour le Canvas",
                            "update_frequency": "once",
                            "avg_monthly_occurrences": 1
                        },
                        {
                            "name": "onboarding_step_completed",
                            "type": "string",
                            "description": "Evenement track a chaque etape d'onboarding completee",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 3
                        }
                    ],
                    "purpose": "Declenchement du Canvas a la creation du compte et suivi de l'onboarding"
                },
                {
                    "entity": "Devices",
                    "attributes": ["platform", "push_enabled", "push_token"],
                    "custom_fields": [],
                    "purpose": "Verification de la disponibilite du push pour l'envoi de la notification J+1"
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
                    "purpose": "Etapes: email de bienvenue, delai 1 jour, decision split (email ouvert?), push de decouverte"
                },
                {
                    "entity": "Content Block",
                    "attributes": ["content_block_id", "name", "content"],
                    "custom_fields": [],
                    "purpose": "Header et footer reutilisables pour les emails de bienvenue"
                }
            ],
            "segments": [
                {
                    "name": "Nouveaux inscrits (J-0)",
                    "filters": [
                        "created_at est dans les dernieres 24 heures",
                        "email_subscribe est opted_in OU push_subscribe est opted_in"
                    ]
                },
                {
                    "name": "Nouveaux inscrits sans onboarding",
                    "filters": [
                        "created_at est dans les 7 derniers jours",
                        "onboarding_completed est false"
                    ]
                }
            ],
            "messaging": {
                "channels": ["email", "push"],
                "trigger_type": "action_based",
                "trigger_details": "Declenche sur l'evenement custom 'account_created'. Email immediat, puis delai 1 jour, Decision Split sur ouverture email, puis push personnalise."
            }
        },
        {
            "use_case": "Relance panier abandonne avec recommandation produit personnalisee",
            "description": "Canvas action-based declenche quand un utilisateur ajoute un produit au panier sans finaliser l'achat dans les 2 heures. Utilise les Catalogues Braze pour afficher les details produits et le Connected Content pour les recommandations personnalisees. Sequence: email H+2, push H+24, SMS H+48 (si non converti).",
            "required_data": [
                {
                    "entity": "User Profile",
                    "attributes": ["external_id", "email", "phone", "first_name", "email_subscribe", "push_subscribe", "language"],
                    "custom_fields": [
                        {
                            "name": "cart_value",
                            "type": "float",
                            "description": "Valeur totale du panier en cours",
                            "update_frequency": "daily"
                        },
                        {
                            "name": "cart_item_count",
                            "type": "integer",
                            "description": "Nombre d'articles dans le panier",
                            "update_frequency": "daily"
                        },
                        {
                            "name": "last_cart_update",
                            "type": "date",
                            "description": "Date de derniere modification du panier",
                            "update_frequency": "daily"
                        }
                    ],
                    "purpose": "Identification de l'utilisateur et personnalisation des messages de relance"
                },
                {
                    "entity": "Custom Events",
                    "attributes": ["name", "time", "properties"],
                    "custom_fields": [
                        {
                            "name": "added_to_cart",
                            "type": "string",
                            "description": "Produit ajoute au panier - proprietes: product_id, product_name, price, category",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 8
                        },
                        {
                            "name": "removed_from_cart",
                            "type": "string",
                            "description": "Produit retire du panier",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 2
                        },
                        {
                            "name": "started_checkout",
                            "type": "string",
                            "description": "Debut du processus de paiement",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 3
                        }
                    ],
                    "purpose": "Tracking du cycle de vie du panier et declenchement de la relance"
                },
                {
                    "entity": "Event Properties",
                    "attributes": ["key", "value"],
                    "custom_fields": [
                        {
                            "name": "product_id",
                            "type": "string",
                            "description": "ID du produit pour le lookup catalogue"
                        },
                        {
                            "name": "product_name",
                            "type": "string",
                            "description": "Nom du produit pour affichage dans le message"
                        },
                        {
                            "name": "price",
                            "type": "float",
                            "description": "Prix unitaire du produit"
                        },
                        {
                            "name": "category",
                            "type": "string",
                            "description": "Categorie du produit pour les recommandations"
                        },
                        {
                            "name": "image_url",
                            "type": "string",
                            "description": "URL de l'image produit"
                        }
                    ],
                    "purpose": "Donnees produit attachees a l'evenement pour personnaliser l'email de relance"
                },
                {
                    "entity": "Purchases",
                    "attributes": ["product_id", "currency", "price", "quantity", "time"],
                    "custom_fields": [],
                    "purpose": "Conversion event pour arreter le Canvas quand l'achat est finalise"
                },
                {
                    "entity": "Catalog",
                    "attributes": ["catalog_name", "catalog_id", "fields"],
                    "custom_fields": [],
                    "purpose": "Catalogue produits pour afficher les details (image, prix, description) dans les emails"
                },
                {
                    "entity": "Catalog Item",
                    "attributes": ["item_id", "fields"],
                    "custom_fields": [],
                    "purpose": "Elements individuels du catalogue produits"
                },
                {
                    "entity": "Connected Content",
                    "attributes": ["url", "method", "headers", "cache_duration"],
                    "custom_fields": [],
                    "purpose": "Appel API de recommandation produit pour suggerer des alternatives dans l'email"
                },
                {
                    "entity": "Canvas",
                    "attributes": ["canvas_id", "canvas_name", "schedule_type"],
                    "custom_fields": [],
                    "purpose": "Orchestration du parcours de relance multi-canal"
                },
                {
                    "entity": "Subscription Groups",
                    "attributes": ["subscription_group_id", "status", "channel"],
                    "custom_fields": [],
                    "purpose": "Verification du consentement SMS avant l'envoi de la relance SMS H+48"
                }
            ],
            "segments": [
                {
                    "name": "Abandonnistes panier (actifs)",
                    "filters": [
                        "A realise l'evenement 'added_to_cart' dans les dernieres 2 heures",
                        "N'a PAS realise l'evenement 'started_checkout' dans les dernieres 2 heures",
                        "cart_value est superieur a 0"
                    ]
                },
                {
                    "name": "Abandonnistes panier recurrents",
                    "filters": [
                        "A realise l'evenement 'added_to_cart' plus de 3 fois dans les 30 derniers jours",
                        "N'a PAS effectue d'achat dans les 30 derniers jours"
                    ]
                },
                {
                    "name": "Exclusion - Acheteurs recents",
                    "filters": [
                        "A effectue un achat dans les dernieres 2 heures"
                    ]
                }
            ],
            "messaging": {
                "channels": ["email", "push", "sms"],
                "trigger_type": "action_based",
                "trigger_details": "Canvas declenche sur l'evenement 'added_to_cart'. Delay de 2h puis verification via Action Paths : si achat realise (exception event 'purchase'), l'utilisateur sort du Canvas. Sinon, envoi du premier message de relance."
            }
        },
        {
            "use_case": "Programme de fidelite avec notifications sur les paliers de points",
            "description": "Systeme de fidelite avec 4 paliers (Bronze, Silver, Gold, Platinum). A chaque achat, les points sont mis a jour via l'API. Un Canvas action-based surveille les changements de palier et envoie des notifications de felicitations + avantages du nouveau statut. Un recapitulatif mensuel est envoye par email.",
            "required_data": [
                {
                    "entity": "User Profile",
                    "attributes": ["external_id", "email", "first_name", "last_name", "email_subscribe", "push_subscribe", "total_revenue", "purchase_count"],
                    "custom_fields": [
                        {
                            "name": "loyalty_tier",
                            "type": "string",
                            "description": "Palier actuel: bronze, silver, gold, platinum",
                            "update_frequency": "monthly"
                        },
                        {
                            "name": "loyalty_points",
                            "type": "integer",
                            "description": "Nombre total de points de fidelite",
                            "update_frequency": "weekly"
                        },
                        {
                            "name": "points_to_next_tier",
                            "type": "integer",
                            "description": "Points restants pour atteindre le palier suivant",
                            "update_frequency": "weekly"
                        },
                        {
                            "name": "loyalty_enrollment_date",
                            "type": "date",
                            "description": "Date d'inscription au programme de fidelite",
                            "update_frequency": "once"
                        },
                        {
                            "name": "loyalty_points_expiring_soon",
                            "type": "integer",
                            "description": "Points expirant dans les 30 prochains jours",
                            "update_frequency": "monthly"
                        },
                        {
                            "name": "previous_loyalty_tier",
                            "type": "string",
                            "description": "Palier precedent (pour detecter les changements)",
                            "update_frequency": "monthly"
                        }
                    ],
                    "purpose": "Donnees de fidelite stockees sur le profil pour segmentation et personnalisation"
                },
                {
                    "entity": "Custom Events",
                    "attributes": ["name", "time", "properties"],
                    "custom_fields": [
                        {
                            "name": "loyalty_tier_changed",
                            "type": "string",
                            "description": "Declencheur: changement de palier fidelite. Proprietes: old_tier, new_tier, total_points",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 0.2
                        },
                        {
                            "name": "points_earned",
                            "type": "string",
                            "description": "Points gagnes lors d'une action. Proprietes: points_amount, source, order_id",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 4
                        },
                        {
                            "name": "points_redeemed",
                            "type": "string",
                            "description": "Points utilises. Proprietes: points_amount, reward_type, reward_name",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 1
                        },
                        {
                            "name": "points_expiring_reminder",
                            "type": "string",
                            "description": "Rappel d'expiration de points (genere par batch job)",
                            "update_frequency": "per_occurrence",
                            "avg_monthly_occurrences": 0.5
                        }
                    ],
                    "purpose": "Evenements du programme de fidelite pour declenchement des Canvas et suivi"
                },
                {
                    "entity": "Event Properties",
                    "attributes": ["key", "value"],
                    "custom_fields": [
                        {
                            "name": "old_tier",
                            "type": "string",
                            "description": "Palier avant le changement"
                        },
                        {
                            "name": "new_tier",
                            "type": "string",
                            "description": "Nouveau palier atteint"
                        },
                        {
                            "name": "points_amount",
                            "type": "integer",
                            "description": "Quantite de points concernes"
                        },
                        {
                            "name": "source",
                            "type": "string",
                            "description": "Source des points (purchase, referral, birthday, promotion)"
                        }
                    ],
                    "purpose": "Details des evenements fidelite pour personnaliser les messages"
                },
                {
                    "entity": "Purchases",
                    "attributes": ["product_id", "price", "quantity", "time", "currency"],
                    "custom_fields": [],
                    "purpose": "Historique d'achats pour le calcul des points et le recapitulatif mensuel"
                },
                {
                    "entity": "Canvas",
                    "attributes": ["canvas_id", "canvas_name", "schedule_type", "status"],
                    "custom_fields": [],
                    "purpose": "Deux Canvas: (1) notification changement de palier, (2) recapitulatif mensuel"
                },
                {
                    "entity": "Canvas Step",
                    "attributes": ["step_id", "step_name", "step_type", "channel"],
                    "custom_fields": [],
                    "purpose": "Etapes: decision split par nouveau palier, messages personnalises par tier, delais"
                },
                {
                    "entity": "Segment",
                    "attributes": ["segment_id", "segment_name", "filters"],
                    "custom_fields": [],
                    "purpose": "Segments par palier de fidelite pour ciblage et reporting"
                },
                {
                    "entity": "Content Block",
                    "attributes": ["content_block_id", "name", "content"],
                    "custom_fields": [],
                    "purpose": "Blocs reutilisables: carte de fidelite, barre de progression, avantages par palier"
                },
                {
                    "entity": "Conversion Event",
                    "attributes": ["event_type", "event_name", "deadline"],
                    "custom_fields": [],
                    "purpose": "Mesure de conversion: achat dans les 7 jours suivant la notification de palier"
                }
            ],
            "segments": [
                {
                    "name": "Membres Bronze",
                    "filters": [
                        "loyalty_tier est egal a 'bronze'",
                        "loyalty_points est entre 0 et 499"
                    ]
                },
                {
                    "name": "Membres Silver",
                    "filters": [
                        "loyalty_tier est egal a 'silver'",
                        "loyalty_points est entre 500 et 1999"
                    ]
                },
                {
                    "name": "Membres Gold",
                    "filters": [
                        "loyalty_tier est egal a 'gold'",
                        "loyalty_points est entre 2000 et 4999"
                    ]
                },
                {
                    "name": "Membres Platinum",
                    "filters": [
                        "loyalty_tier est egal a 'platinum'",
                        "loyalty_points est superieur ou egal a 5000"
                    ]
                },
                {
                    "name": "Points expirant bientot",
                    "filters": [
                        "loyalty_points_expiring_soon est superieur a 0",
                        "A realise l'evenement 'points_expiring_reminder' dans les dernieres 24h"
                    ]
                }
            ],
            "messaging": {
                "channels": ["email", "push", "in_app_message"],
                "trigger_type": "action_based",
                "trigger_details": "Canvas 1 (palier): declenche sur 'loyalty_tier_changed', Decision Split par new_tier, email + push + in-app de felicitations avec avantages du nouveau palier. Canvas 2 (mensuel): schedule le 1er du mois, email recapitulatif avec points gagnes/depenses, progression vers le palier suivant."
            }
        }
    ],
    "data_hierarchy": [
        {
            "entity": "User Profile",
            "attributes_used": ["external_id", "email", "phone", "first_name", "last_name", "email_subscribe", "push_subscribe", "created_at", "language", "total_revenue", "purchase_count"],
            "children": [
                {
                    "entity": "Custom Attributes",
                    "attributes_used": ["onboarding_completed", "signup_source", "welcome_offer_code", "cart_value", "cart_item_count", "last_cart_update", "loyalty_tier", "loyalty_points", "points_to_next_tier", "loyalty_enrollment_date", "loyalty_points_expiring_soon", "previous_loyalty_tier"],
                    "children": []
                },
                {
                    "entity": "Custom Events",
                    "attributes_used": ["account_created", "onboarding_step_completed", "added_to_cart", "removed_from_cart", "started_checkout", "loyalty_tier_changed", "points_earned", "points_redeemed", "points_expiring_reminder"],
                    "children": [
                        {
                            "entity": "Event Properties",
                            "attributes_used": ["product_id", "product_name", "price", "category", "image_url", "old_tier", "new_tier", "points_amount", "source"],
                            "children": []
                        }
                    ]
                },
                {
                    "entity": "Purchases",
                    "attributes_used": ["product_id", "currency", "price", "quantity", "time"],
                    "children": []
                },
                {
                    "entity": "Devices",
                    "attributes_used": ["platform", "push_enabled", "push_token"],
                    "children": []
                },
                {
                    "entity": "Subscription Groups",
                    "attributes_used": ["subscription_group_id", "status", "channel"],
                    "children": []
                }
            ]
        },
        {
            "entity": "Canvas",
            "attributes_used": ["canvas_id", "canvas_name", "schedule_type", "status"],
            "children": [
                {
                    "entity": "Canvas Step",
                    "attributes_used": ["step_id", "step_name", "step_type", "channel"],
                    "children": []
                }
            ]
        },
        {
            "entity": "Segment",
            "attributes_used": ["segment_id", "segment_name", "filters"],
            "children": [
                {
                    "entity": "Segment Filter",
                    "attributes_used": ["filter_type", "attribute_or_event", "operator", "value"],
                    "children": []
                }
            ]
        },
        {
            "entity": "Catalog",
            "attributes_used": ["catalog_name", "catalog_id", "fields"],
            "children": [
                {
                    "entity": "Catalog Item",
                    "attributes_used": ["item_id", "fields"],
                    "children": []
                }
            ]
        },
        {
            "entity": "Content Block",
            "attributes_used": ["content_block_id", "name", "content"],
            "children": []
        },
        {
            "entity": "Connected Content",
            "attributes_used": ["url", "method", "headers", "cache_duration"],
            "children": []
        },
        {
            "entity": "Conversion Event",
            "attributes_used": ["event_type", "event_name", "deadline"],
            "children": []
        }
    ],
    "data_points_optimization": [
        "Considerer l'utilisation d'event properties au lieu des custom attributes 'cart_value', 'cart_item_count' et 'last_cart_update' — ces donnees volatiles changent a chaque interaction panier et generent beaucoup de data points",
        "L'attribut 'previous_loyalty_tier' peut etre remplace par une event property sur l'evenement 'loyalty_tier_changed' (old_tier) — economie de ~100K data points/mois pour 100K MAU",
        "Utiliser un Catalog Braze pour les donnees produits au lieu de stocker les details dans des custom attributes",
        "Les event properties (product_id, product_name, price, category) sont GRATUITES — continuer a les privilegier pour les donnees contextuelles"
    ],
    "mermaid_diagram": """graph TD
    UP[User Profile] --> CA[Custom Attributes]
    UP --> CE[Custom Events]
    UP --> PU[Purchases]
    UP --> DV[Devices]
    UP --> SG[Subscription Groups]
    CE --> EP[Event Properties]

    CV[Canvas] --> CS[Canvas Step]
    CV --> CVR[Canvas Variant]

    SEG[Segment] --> SF[Segment Filter]
    SF -.->|filtre sur| CA
    SF -.->|filtre sur| CE
    SF -.->|filtre sur| PU

    CAT[Catalog] --> CI[Catalog Item]
    CB[Content Block]
    CC[Connected Content]
    CONV[Conversion Event]

    CV -.->|cible| SEG
    CS -.->|utilise| CB
    CS -.->|utilise| CC
    CS -.->|utilise| CAT
    CV -.->|mesure| CONV

    CA --- CA_LIST["onboarding_completed<br/>signup_source<br/>welcome_offer_code<br/>cart_value,cart_item_count<br/>loyalty_tier,loyalty_points<br/>points_to_next_tier"]
    CE --- CE_LIST["account_created<br/>added_to_cart, started_checkout<br/>loyalty_tier_changed<br/>points_earned,points_redeemed"]

    style UP fill:#2196F3,color:white
    style CA fill:#4CAF50,color:white
    style CE fill:#4CAF50,color:white
    style EP fill:#4CAF50,color:white
    style PU fill:#4CAF50,color:white
    style DV fill:#4CAF50,color:white
    style SG fill:#4CAF50,color:white
    style CV fill:#FF9800,color:white
    style CS fill:#FF9800,color:white
    style CVR fill:#FF9800,color:white
    style SEG fill:#9C27B0,color:white
    style SF fill:#9C27B0,color:white
    style CAT fill:#00BCD4,color:white
    style CI fill:#00BCD4,color:white
    style CB fill:#00BCD4,color:white
    style CC fill:#00BCD4,color:white
    style CONV fill:#F44336,color:white
    style CA_LIST fill:#E8F5E9,color:#333
    style CE_LIST fill:#E8F5E9,color:#333"""
}
