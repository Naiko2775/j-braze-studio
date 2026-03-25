"""Estimation des data points Braze a partir d'un resultat d'analyse."""

import math

# Attributs standard Braze qui ne consomment PAS de data points
FREE_STANDARD_ATTRIBUTES = {
    "email",
    "first_name",
    "last_name",
    "home_city",
    "country",
    "date_of_birth",
    "gender",
    "language",
    "phone_number",
    "push_token",
    "time_zone",
    # Variantes courantes (aliases)
    "phone",
    "city",
    "dob",
    "birthdate",
    "timezone",
    "push_tokens",
    "email_subscribe",
    "push_subscribe",
    "external_id",
    "created_at",
    "total_revenue",
    "purchase_count",
}

# Multiplicateur de frequence -> nombre de mises a jour par mois
FREQUENCY_MULTIPLIER = {
    "once": 0.05,       # ~1x sur la vie du profil, amortie sur le mois
    "rarely": 0.1,
    "monthly": 1,
    "weekly": 4.33,
    "daily": 30,
    "per_occurrence": 1,  # sera multiplie par avg_monthly_occurrences
}

# Grille indicative de cout Braze (source : grilles publiques 2025)
COST_TIERS = [
    {"tier": "Starter", "max_dp": 5_000_000, "range": "$0-$500/mois", "note": "Jusqu'a 5M data points inclus"},
    {"tier": "Growth", "max_dp": 25_000_000, "range": "$500-$1,500/mois", "note": "Typiquement 5M-25M data points"},
    {"tier": "Pro", "max_dp": 100_000_000, "range": "$1,500-$5,000/mois", "note": "Typiquement 25M-100M data points"},
    {"tier": "Enterprise", "max_dp": float("inf"), "range": "$5,000+/mois", "note": "Plus de 100M data points, tarification sur mesure"},
]


def _is_free_attribute(name: str) -> bool:
    """Verifie si un attribut est un attribut standard gratuit Braze."""
    return name.lower().strip() in FREE_STANDARD_ATTRIBUTES


def _get_frequency_multiplier(frequency: str) -> float:
    """Retourne le multiplicateur mensuel pour une frequence donnee."""
    return FREQUENCY_MULTIPLIER.get(frequency, 1)


def _extract_custom_attributes(analysis_result: dict) -> list[dict]:
    """Extrait tous les custom attributes uniques du resultat d'analyse."""
    attrs = {}
    for uc in analysis_result.get("use_case_analysis", []):
        for rd in uc.get("required_data", []):
            # Attributs standard listes dans 'attributes'
            for attr_name in rd.get("attributes", []):
                if attr_name not in attrs:
                    attrs[attr_name] = {
                        "name": attr_name,
                        "type": "string",
                        "is_free": _is_free_attribute(attr_name),
                        "frequency": "once",
                        "source_entity": rd.get("entity", ""),
                    }
            # Custom fields
            for cf in rd.get("custom_fields", []):
                name = cf.get("name", "")
                if name and name not in attrs:
                    attrs[name] = {
                        "name": name,
                        "type": cf.get("type", "string"),
                        "is_free": _is_free_attribute(name),
                        "frequency": cf.get("update_frequency", "monthly"),
                        "source_entity": rd.get("entity", ""),
                        "description": cf.get("description", ""),
                    }
    return list(attrs.values())


def _extract_custom_events(analysis_result: dict) -> list[dict]:
    """Extrait tous les custom events uniques du resultat d'analyse."""
    events = {}
    for uc in analysis_result.get("use_case_analysis", []):
        for rd in uc.get("required_data", []):
            entity = rd.get("entity", "")
            if entity not in ("Custom Events", "Custom Event"):
                continue
            for cf in rd.get("custom_fields", []):
                name = cf.get("name", "")
                if name and name not in events:
                    events[name] = {
                        "name": name,
                        "description": cf.get("description", ""),
                        "avg_monthly_occurrences": cf.get("avg_monthly_occurrences", 2),
                    }
    return list(events.values())


def _compute_cost_estimate(total_monthly: int) -> dict:
    """Determine le tier de cout indicatif."""
    for tier in COST_TIERS:
        if total_monthly <= tier["max_dp"]:
            return {
                "tier": tier["tier"],
                "estimated_monthly_cost_range": tier["range"],
                "note": f"Estimation indicative basee sur les grilles publiques Braze 2025. {tier['note']}.",
            }
    # Fallback
    return COST_TIERS[-1]


def _generate_recommendations(
    attributes: list[dict],
    events: list[dict],
    user_volume: int,
) -> list[str]:
    """Genere des recommandations d'optimisation des data points."""
    recommendations = []

    # Detecter les attributs volatiles qui pourraient etre des event properties
    volatile_keywords = [
        "last_", "latest_", "recent_", "current_", "cart_", "session_",
        "temp_", "viewed", "clicked",
    ]
    for attr in attributes:
        if attr["is_free"]:
            continue
        name_lower = attr["name"].lower()
        for kw in volatile_keywords:
            if kw in name_lower:
                freq = attr.get("frequency", "monthly")
                mult = _get_frequency_multiplier(freq)
                savings = int(user_volume * mult)
                if savings > 0:
                    recommendations.append(
                        f"Considerer l'utilisation d'event properties au lieu du custom attribute "
                        f"'{attr['name']}' (economie potentielle ~{_format_number(savings)} data points/mois)"
                    )
                break

    # Detecter les attributs de type array
    for attr in attributes:
        if attr.get("type") in ("array", "object") and not attr["is_free"]:
            recommendations.append(
                f"L'attribut '{attr['name']}' est de type {attr['type']} — chaque element "
                f"du tableau/objet compte comme 1 data point lors de la mise a jour. "
                f"Considerer l'utilisation d'un Catalog Braze ou de nested objects."
            )

    # Recommandation sur les mises a jour trop frequentes
    for attr in attributes:
        if attr.get("frequency") == "daily" and not attr["is_free"]:
            monthly_dp = user_volume * 30
            if monthly_dp > 1_000_000:
                recommendations.append(
                    f"L'attribut '{attr['name']}' est mis a jour quotidiennement, "
                    f"ce qui genere ~{_format_number(monthly_dp)} data points/mois. "
                    f"Verifier si une frequence hebdomadaire ou mensuelle serait suffisante."
                )

    # Recommandation Connected Content / Catalogs pour donnees de reference
    if len([a for a in attributes if not a["is_free"]]) > 15:
        recommendations.append(
            "Vous avez plus de 15 custom attributes — considerer l'utilisation de Connected "
            "Content ou Braze Catalogs pour les donnees de reference (produits, magasins, etc.) "
            "afin de reduire la consommation de data points."
        )

    # Rappel sur les event properties gratuites
    if events:
        recommendations.append(
            "Les event properties sont GRATUITES et ne consomment aucun data point. "
            "Privilegier le passage de donnees contextuelles via event properties plutot "
            "que via custom attributes quand c'est possible."
        )

    return recommendations


def _format_number(n: int) -> str:
    """Formate un nombre avec des separateurs de milliers."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def estimate_data_points(
    analysis_result: dict,
    user_volume: int,
    update_frequency: dict | None = None,
) -> dict:
    """Estime les data points Braze a partir du resultat d'analyse.

    Args:
        analysis_result: Resultat de l'analyse Claude (use_case_analysis, data_hierarchy, etc.)
        user_volume: Nombre total d'utilisateurs actifs mensuels (MAU)
        update_frequency: Frequence de mise a jour par categorie, ex:
            {"profile": "monthly", "behavior": "daily", "purchase": "weekly"}

    Returns:
        Dictionnaire avec summary, breakdown, recommendations, cost_estimate.
    """
    update_frequency = update_frequency or {}

    # Mapping de categories d'attributs vers frequences par defaut
    category_defaults = {
        "profile": update_frequency.get("profile", "monthly"),
        "behavior": update_frequency.get("behavior", "weekly"),
        "purchase": update_frequency.get("purchase", "weekly"),
    }

    # Extraction
    all_attributes = _extract_custom_attributes(analysis_result)
    all_events = _extract_custom_events(analysis_result)

    # Application des frequences par categorie
    behavior_keywords = [
        "cart_", "last_", "session_", "viewed", "clicked", "active",
        "onboarding", "login", "visit",
    ]
    purchase_keywords = [
        "purchase", "order", "revenue", "payment", "transaction",
        "loyalty_points", "points_",
    ]

    for attr in all_attributes:
        if attr["is_free"]:
            attr["frequency"] = "once"
            continue

        # Si l'attribut a deja une frequence definie par Claude, la garder
        if attr.get("frequency") and attr["frequency"] != "monthly":
            continue

        name_lower = attr["name"].lower()
        # Classifier par categorie
        if any(kw in name_lower for kw in behavior_keywords):
            attr["frequency"] = category_defaults["behavior"]
        elif any(kw in name_lower for kw in purchase_keywords):
            attr["frequency"] = category_defaults["purchase"]
        else:
            attr["frequency"] = category_defaults["profile"]

    # Calcul des data points par attribut
    attributes_breakdown = []
    total_attr_dp = 0

    for attr in all_attributes:
        if attr["is_free"]:
            attributes_breakdown.append({
                "name": attr["name"],
                "type": attr.get("type", "string"),
                "frequency": "N/A (gratuit)",
                "monthly_data_points": 0,
                "is_free": True,
            })
            continue

        freq = attr.get("frequency", "monthly")
        multiplier = _get_frequency_multiplier(freq)
        monthly_dp = int(user_volume * multiplier)
        total_attr_dp += monthly_dp

        attributes_breakdown.append({
            "name": attr["name"],
            "type": attr.get("type", "string"),
            "frequency": freq,
            "monthly_data_points": monthly_dp,
            "is_free": False,
        })

    # Calcul des data points par event
    events_breakdown = []
    total_events_dp = 0

    for event in all_events:
        avg_occ = event.get("avg_monthly_occurrences", 2)
        monthly_dp = int(user_volume * avg_occ)
        total_events_dp += monthly_dp

        events_breakdown.append({
            "name": event["name"],
            "frequency": "per_occurrence",
            "avg_monthly_occurrences": avg_occ,
            "monthly_data_points": monthly_dp,
        })

    # Comptages
    free_count = sum(1 for a in attributes_breakdown if a["is_free"])
    custom_attr_count = sum(1 for a in attributes_breakdown if not a["is_free"])
    custom_events_count = len(events_breakdown)

    total_monthly = total_attr_dp + total_events_dp
    total_yearly = total_monthly * 12

    # Recommandations
    recommendations = _generate_recommendations(all_attributes, all_events, user_volume)

    # Estimation de cout
    cost_estimate = _compute_cost_estimate(total_monthly)

    # Tri du breakdown : payants d'abord (par cout decroissant), puis gratuits
    attributes_breakdown.sort(key=lambda x: (x["is_free"], -x["monthly_data_points"]))
    events_breakdown.sort(key=lambda x: -x["monthly_data_points"])

    return {
        "summary": {
            "custom_attributes_count": custom_attr_count,
            "custom_events_count": custom_events_count,
            "free_attributes_count": free_count,
            "total_monthly_data_points": total_monthly,
            "total_yearly_data_points": total_yearly,
        },
        "breakdown": {
            "custom_attributes": attributes_breakdown,
            "custom_events": events_breakdown,
        },
        "recommendations": recommendations,
        "cost_estimate": cost_estimate,
    }
