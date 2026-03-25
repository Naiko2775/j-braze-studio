"""Generateur de bannieres Liquid via Claude.

Porte la logique d'appel Anthropic depuis braze/src/App.jsx
(SYSTEM_PROMPT, enrichissement brief, parsing JSON) cote serveur
en utilisant le SDK Python au lieu de fetch client-side.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from services.liquid.templates import TEMPLATES, get_template

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt -- porte depuis App.jsx SYSTEM_PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Tu es un agent expert en creation de contenus marketing personnalises pour Braze.
Tu maitrises les bannieres, emails complets, notifications push et SMS.

Tu recois un brief creatif et tu dois generer un JSON structure pour remplir un template.

== TEMPLATES BANNIERES ==
- hero_banner : Grande banniere promo (headline, subheadline, CTA, image)
- product_card : Mise en avant produit (product_name, price, old_price, badge, CTA)
- countdown : Offre limitee (headline, end_date, CTA)
- cta_simple : Banniere minimaliste (headline, CTA)
- testimonial : Social proof (quote, author, role, CTA)

== TEMPLATES EMAIL COMPLETS ==
- welcome_email : Email de bienvenue (header, hero, message, 3 avantages, CTA, footer desabonnement)
- abandoned_cart_email : Relance panier (header, rappel, boucle produits, CTA, recommandations, footer)
- loyalty_email : Programme fidelite (header, statut tier, points, barre progression, avantages, CTA, footer)
- post_purchase_email : Confirmation commande (header, recap produits, cross-sell, NPS survey, footer)
- winback_email : Reconquete (header, offre -20%, compteur expiration, best-sellers, CTA, footer)

== TEMPLATE PUSH ==
- push_notification : Notification push (titre max 50 chars, corps max 150 chars, image, deep link, action buttons)

== TEMPLATE SMS ==
- sms_message : SMS (texte max 160 chars total, lien court, opt-out STOP)

REGLES GENERALES :
- headline <= 60 caracteres
- subheadline <= 120 caracteres
- Utilise la personnalisation Liquid Braze ({{ ${first_name} }}, {{ ${city} }}, etc.) quand pertinent
- Ajoute TOUJOURS un filtre default pour les variables Liquid : {{ ${first_name} | default: 'cher client' }}
- Respecte le ton demande (premium, friendly, urgent, etc.)
- Si des couleurs sont specifiees, utilise-les. Sinon propose des couleurs harmonieuses.

REGLES EMAIL :
- Le HTML email DOIT utiliser des TABLES (pas de divs flex/grid) pour la compatibilite email clients (Outlook, Gmail, Apple Mail)
- Structure : <table role="presentation"> avec cellpadding/cellspacing
- CSS inline uniquement (pas de <style> sauf pour les media queries responsive)
- Largeur max 600px avec un wrapper background
- Inclure les media queries pour le responsive (@media max-width: 600px)
- Toujours inclure un lien de desabonnement {{ subscription_management_url }} dans le footer
- Utiliser les conditions Liquid ({% if %}, {% elsif %}, {% for %}) pour la personnalisation avancee

REGLES PUSH :
- Titre : max 50 caracteres, percutant
- Corps : max 150 caracteres, clair et incitatif
- Toujours inclure un deep_link
- Max 2 action buttons

REGLES SMS :
- Message TOTAL max 160 caracteres (incluant le lien et le STOP)
- Toujours inclure "STOP au XXXXX" pour l'opt-out
- Lien court obligatoire

Tu dois TOUJOURS repondre UNIQUEMENT avec un JSON valide, sans markdown, sans backticks, sans explication.

Schema JSON attendu :
{
  "template": "nom_du_template",
  "params": {
    "headline": "string",
    "subheadline": "string (optionnel selon template)",
    "cta_text": "string",
    "cta_url": "string",
    "cta_color": "#hex",
    "bg_color": "#hex",
    "text_color": "#hex",
    "image_url": "string (optionnel)",
    "badge": "string (optionnel)",
    "product_name": "string (optionnel, pour product_card)",
    "price": "string (optionnel)",
    "old_price": "string (optionnel)",
    "quote": "string (optionnel, pour testimonial)",
    "author": "string (optionnel)",
    "role": "string (optionnel)",
    "end_date": "string (optionnel, pour countdown)",
    "title": "string (optionnel, pour push)",
    "body": "string (optionnel, pour push)",
    "deep_link": "string (optionnel, pour push)",
    "message_text": "string (optionnel, pour sms)",
    "short_link": "string (optionnel, pour sms)",
    "order_number": "string (optionnel, pour post_purchase)",
    "offer_code": "string (optionnel, pour winback)"
  },
  "liquid_code": "Le code HTML+Liquid complet, pret a copier dans Braze. Pour les bannieres : inline CSS responsive. Pour les emails : tables HTML completes avec doctype. Pour les push : JSON avec title/body/deep_link. Pour les SMS : texte brut avec Liquid.",
  "personalization_notes": "Explication courte des variables Liquid utilisees",
  "ab_variants": [
    { "variant": "A", "headline": "...", "rationale": "..." },
    { "variant": "B", "headline": "...", "rationale": "..." }
  ]
}"""

# ---------------------------------------------------------------------------
# Mock result for demo mode (no API key)
# ---------------------------------------------------------------------------

DEMO_RESULT: dict[str, Any] = {
    "template": "hero_banner",
    "params": {
        "headline": "Bienvenue {{ ${first_name} | default: 'cher client' }} !",
        "subheadline": "Decouvrez nos offres exclusives selectionnees pour vous",
        "cta_text": "Decouvrir",
        "cta_url": "/offres",
        "cta_color": "#f00a0a",
        "bg_color": "#040066",
        "text_color": "#ffffff",
    },
    "liquid_code": (
        '<div style="background:#040066;color:#ffffff;padding:48px 32px;'
        'text-align:center;border-radius:12px;font-family:sans-serif;">\n'
        '  <h1 style="font-size:28px;font-weight:800;margin-bottom:12px;">'
        "Bienvenue {{ ${first_name} | default: 'cher client' }} !</h1>\n"
        '  <p style="font-size:16px;opacity:0.85;max-width:480px;margin:0 auto 24px;">'
        "Decouvrez nos offres exclusives selectionnees pour vous</p>\n"
        '  <a href="/offres" style="display:inline-block;background:#f00a0a;'
        'color:#fff;padding:12px 32px;border-radius:6px;font-weight:700;'
        'text-decoration:none;">Decouvrir</a>\n'
        "</div>"
    ),
    "personalization_notes": (
        "Utilise ${first_name} avec fallback 'cher client' pour la personnalisation du prenom."
    ),
    "ab_variants": [
        {
            "variant": "A",
            "headline": "Bienvenue {{ ${first_name} | default: 'cher client' }} !",
            "rationale": "Ton chaleureux et accueillant avec personnalisation",
        },
        {
            "variant": "B",
            "headline": "Vos offres exclusives vous attendent",
            "rationale": "Focus sur la valeur et l'exclusivite, sans personnalisation",
        },
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_banner(
    brief: str,
    template_type: str | None = None,
    channel: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Genere une banniere a partir d'un brief creatif.

    - Construit le prompt (brief + info template si specifie)
    - Appelle Claude via le SDK Python (server-side)
    - Parse la reponse JSON
    - Retourne le resultat structure

    En mode demo (pas de cle API), retourne un resultat mock.

    Returns:
        dict avec les cles: template, params, liquid_code,
        personalization_notes, ab_variants, model_used
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("Pas de cle API Anthropic -- mode demo")
        return {**DEMO_RESULT, "model_used": "demo"}

    # Enrichissement du brief avec le template si specifie
    # (porte depuis App.jsx: enrichedBrief)
    user_message = brief
    if template_type:
        tpl = get_template(template_type)
        if tpl:
            user_message = (
                f"Template souhaite : {template_type} ({tpl['name']} - {tpl['description']}). "
                f"Champs attendus : {', '.join(tpl['structure']['required'])}. "
                f"Brief : {brief}"
            )
        else:
            user_message = f"Template souhaite : {template_type}. Brief : {brief}"

    if channel:
        user_message += f"\nCanal cible : {channel}"

    # Appel Claude via SDK Python (server-side)
    from services.claude_client import get_claude_client, get_default_model

    client = get_claude_client()
    model_name = model or get_default_model()

    response = client.messages.create(
        model=model_name,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extraction du texte de la reponse
    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    # Parsing JSON (nettoyage backticks eventuels comme dans App.jsx)
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Echec parsing JSON Claude: %s\nTexte brut: %s", exc, cleaned[:500])
        raise ValueError(f"La reponse Claude n'est pas un JSON valide: {exc}") from exc

    # Validation minimale de la structure
    if "template" not in parsed or "params" not in parsed:
        raise ValueError(
            "La reponse Claude ne contient pas les cles requises (template, params)"
        )

    parsed["model_used"] = model_name
    return parsed
