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

from services.liquid.templates import (
    TEMPLATES,
    get_brand_charter,
    get_template,
    get_tone,
)

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

== CHARTE DE MARQUE ==
- Si une charte de marque est fournie, ses couleurs, ses typographies, ses principes et son style d'imagerie s'appliquent OBLIGATOIREMENT.
- Les couleurs de la charte PRIMENT sur toute couleur ecrite en clair dans le brief : en cas de conflit, c'est la charte qui gagne.
- Renseigne bg_color / text_color / cta_color avec les couleurs de la charte (fond = background, texte = text, CTA = primary ou secondary selon le meilleur contraste).
- Reprends les familles de polices de la charte dans le CSS inline (font-family) et respecte son style d'imagerie.

== TON DE VOIX ==
- Si un ton de voix est fourni, il PRIME sur tout ton demande en clair dans le brief : en cas de conflit, c'est le ton selectionne qui gagne.
- Applique son registre (tutoiement ou vouvoiement, longueur des phrases, emojis ou non), sa posture et son style de CTA.
- Le ton doit etre VISIBLE dans le headline, le subheadline, le corps de texte, le libelle du CTA et les deux variantes A/B.

== CONFORMITE ALCOOL ==
- Pour une marque d'alcool, toute copie marketing DOIT porter la mention de moderation : "L'abus d'alcool est dangereux pour la sante. A consommer avec moderation." (dans le visuel de la banniere, le footer de l'email, ou en fin de message pour un push / SMS ; forme courte "A consommer avec moderation." si la limite de caracteres l'impose).
- Ne jamais s'adresser aux mineurs, ne jamais evoquer un public de moins de 18 ans, ne jamais inciter a une consommation excessive.

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
  "brand_charter": "identifiant de la charte de marque appliquee (string, ou null si aucune)",
  "tone_of_voice": "identifiant du ton de voix applique (string, ou null si aucun)",
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
# Charte de marque & ton de voix -- mise en forme pour le prompt
# ---------------------------------------------------------------------------


def _format_charter_brief(charter: dict[str, Any]) -> str:
    """Formate la charte de marque resolue pour l'ajouter au message utilisateur."""
    colors = charter.get("colors", {})
    fonts = charter.get("fonts", {})
    lines = [
        "",
        f"Charte de marque imposee : {charter.get('label', charter.get('id'))}"
        f" ({charter.get('description', '')})",
        "Couleurs (elles PRIMENT sur toute couleur citee dans le brief) :",
        f"- primaire : {colors.get('primary')}",
        f"- secondaire : {colors.get('secondary')}",
        f"- fond : {colors.get('background')}",
        f"- texte : {colors.get('text')}",
        f"Typographies : titres = {fonts.get('heading')} "
        f"(font-family: {fonts.get('heading_stack')}) ; "
        f"textes = {fonts.get('body')} "
        f"(font-family: {fonts.get('body_stack')})",
        f"Principes : {', '.join(charter.get('principles', []))}",
        f"Imagerie : {charter.get('imagery', '')}",
        f"Avertissement : {charter.get('avertissement', '')}",
    ]
    return "\n".join(lines)


def _format_tone_brief(tone: dict[str, Any]) -> str:
    """Formate le ton de voix resolu pour l'ajouter au message utilisateur."""
    lines = [
        "",
        f"Ton de voix impose : {tone.get('label', tone.get('id'))}"
        f" ({tone.get('description', '')})",
        f"Registre : {tone.get('register')}",
        f"Posture : {tone.get('posture')}",
        f"Style de CTA : {tone.get('cta_style')}",
        f"Exemples de CTA : {', '.join(tone.get('cta_examples', []))}",
        f"A eviter : {', '.join(tone.get('avoid', []))}",
    ]
    for rule in tone.get("compliance", []):
        lines.append(f"Conformite : {rule}")
    lines.append(
        "Ce ton PRIME sur tout ton demande en clair dans le brief et doit etre "
        "visible dans le headline, le corps, le CTA et les variantes A/B."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode demo : la selection doit rester visible sans cle API
# ---------------------------------------------------------------------------

# Copy de demonstration par ton, pour que le mode demo reflete reellement le
# ton selectionne (un selecteur sans effet visible = fonctionnalite ratee).
DEMO_TONE_COPY: dict[str, dict[str, Any]] = {
    "corporate_institutional": {
        "headline": "Bonjour {{ ${first_name} | default: 'cher client' }}",
        "subheadline": (
            "Decouvrez les engagements qui guident chacune de nos maisons, "
            "de la vigne au verre."
        ),
        "cta_text": "Decouvrir nos engagements",
        "cta_url": "/engagements",
        "notes": (
            "Vouvoiement et phrases completes : la variable ${first_name} garde un "
            "fallback neutre 'cher client'."
        ),
        "variants": [
            ("A", "Bonjour {{ ${first_name} | default: 'cher client' }}", "Personnalisation sobre, registre institutionnel"),
            ("B", "Nos engagements, en toute transparence", "Sans personnalisation, focus sur la posture responsable"),
        ],
    },
    "ricard_convivial": {
        "headline": "{{ ${first_name} | default: 'Salut' }}, la tablee t'attend !",
        "subheadline": "Du soleil, des amis, et le Sud a portee de verre.",
        "cta_text": "Rejoins la tablee",
        "cta_url": "/rejoindre",
        "notes": (
            "Tutoiement et phrases courtes : ${first_name} avec fallback 'Salut' "
            "pour garder le ton complice meme sans prenom connu."
        ),
        "variants": [
            ("A", "{{ ${first_name} | default: 'Salut' }}, la tablee t'attend !", "Interpellation directe, energie et proximite"),
            ("B", "Le Sud commence a cette table", "Promesse d'ambiance, sans personnalisation"),
        ],
    },
}


def _readable_text_on(hex_color: str, fallback: str = "#FFFFFF") -> str:
    """Retourne #FFFFFF ou #1A1A1A selon la luminance du fond donne."""
    value = (hex_color or "").lstrip("#")
    if len(value) != 6:
        return fallback
    try:
        r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return fallback
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#1A1A1A" if luminance > 0.6 else "#FFFFFF"


def _apply_demo_charter(
    base: dict[str, Any],
    charter: dict[str, Any] | None,
    tone: dict[str, Any] | None,
) -> dict[str, Any]:
    """Reconstruit le resultat de demo avec la charte et le ton selectionnes.

    Sans cle API, c'est le seul rendu que voit l'utilisateur : il doit donc
    refleter les deux selecteurs (couleurs + copy), pas juste les echo.
    """
    if charter is None and tone is None:
        return dict(base)

    result = json.loads(json.dumps(base))
    params = result["params"]

    copy = DEMO_TONE_COPY.get(tone.get("id")) if tone else None
    if copy:
        params["headline"] = copy["headline"]
        params["subheadline"] = copy["subheadline"]
        params["cta_text"] = copy["cta_text"]
        params["cta_url"] = copy["cta_url"]
        result["personalization_notes"] = copy["notes"]
        result["ab_variants"] = [
            {"variant": v, "headline": h, "rationale": r} for v, h, r in copy["variants"]
        ]

    if charter:
        colors = charter.get("colors", {})
        fonts = charter.get("fonts", {})
        params["bg_color"] = colors.get("background", params["bg_color"])
        params["text_color"] = colors.get("text", params["text_color"])
        params["cta_color"] = colors.get("primary", params["cta_color"])
        params["heading_font"] = fonts.get("heading_stack", "sans-serif")
        params["body_font"] = fonts.get("body_stack", "sans-serif")

    moderation = (tone or {}).get("moderation_message")
    if charter and not moderation:
        moderation = (
            "L'abus d'alcool est dangereux pour la sante. A consommer avec moderation."
        )

    result["liquid_code"] = _build_demo_liquid(params, moderation)
    return result


def _build_demo_liquid(params: dict[str, Any], moderation: str | None) -> str:
    """Regenere le HTML de demo a partir des params (couleurs + polices charte)."""
    heading_font = params.get("heading_font", "sans-serif")
    body_font = params.get("body_font", "sans-serif")
    cta_color = params.get("cta_color", "#f00a0a")
    cta_text_color = _readable_text_on(cta_color)
    moderation_block = ""
    if moderation:
        moderation_block = (
            f'  <p style="font-size:11px;opacity:0.7;margin:20px 0 0;'
            f'font-family:{body_font};">{moderation}</p>\n'
        )
    return (
        f'<div style="background:{params.get("bg_color")};'
        f'color:{params.get("text_color")};padding:48px 32px;text-align:center;'
        f'border-radius:12px;font-family:{body_font};">\n'
        f'  <h1 style="font-size:28px;font-weight:800;margin-bottom:12px;'
        f'font-family:{heading_font};">{params.get("headline")}</h1>\n'
        f'  <p style="font-size:16px;opacity:0.85;max-width:480px;'
        f'margin:0 auto 24px;">{params.get("subheadline")}</p>\n'
        f'  <a href="{params.get("cta_url")}" style="display:inline-block;'
        f'background:{cta_color};color:{cta_text_color};padding:12px 32px;'
        f'border-radius:6px;font-weight:700;text-decoration:none;'
        f'font-family:{body_font};">{params.get("cta_text")}</a>\n'
        f"{moderation_block}"
        "</div>"
    )



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_banner(
    brief: str,
    template_type: str | None = None,
    channel: str | None = None,
    brand_charter: str | None = None,
    tone_of_voice: str | None = None,
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
        personalization_notes, ab_variants, model_used,
        brand_charter, tone_of_voice
    """
    # Catalogue serveur : la charte et le ton sont resolus cote serveur pour
    # que le resultat porte les valeurs canoniques (couleurs, avertissement)
    # et pas seulement un identifiant renvoye par le modele.
    charter = get_brand_charter(brand_charter) if brand_charter else None
    tone = get_tone(tone_of_voice) if tone_of_voice else None
    # Un identifiant inconnu resolvait a None sans bruit : la generation
    # reussissait sans charte et le badge disparaissait, sans rien signaler.
    if brand_charter and charter is None:
        logger.warning("Charte de marque inconnue ignoree : %r", brand_charter)
    if tone_of_voice and tone is None:
        logger.warning("Ton de voix inconnu ignore : %r", tone_of_voice)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("Pas de cle API Anthropic -- mode demo")
        return {
            **_apply_demo_charter(DEMO_RESULT, charter, tone),
            "model_used": "demo",
            "brand_charter": charter,
            "tone_of_voice": tone,
        }

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

    if charter:
        user_message += _format_charter_brief(charter)

    if tone:
        user_message += _format_tone_brief(tone)

    # Appel Claude via SDK Python (server-side)
    from services.claude_client import get_claude_client, get_default_model

    client = get_claude_client()
    model_name = model or get_default_model()

    response = client.messages.create(
        model=model_name,
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Opus 5 reflechit par defaut, et les tokens de reflexion sont decomptes
    # de max_tokens : un budget trop bas tronque le JSON en pleine chaine et
    # produit un "Unterminated string" incomprehensible cote utilisateur.
    if response.stop_reason == "max_tokens":
        raise ValueError(
            "Reponse Claude tronquee : la limite max_tokens a ete atteinte "
            "avant la fin du JSON. Augmenter max_tokens ou raccourcir le brief."
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
    # Le routeur ne renvoie que {id, result, created_at} : tout ce qui n'est
    # pas dans `parsed` est invisible pour le front.
    # Ecrasement et non setdefault : le schema JSON demande ces cles a Claude,
    # donc sans selection le modele peut inventer un identifiant, que l'UI
    # afficherait comme une charte reellement appliquee.
    parsed["brand_charter"] = charter
    parsed["tone_of_voice"] = tone
    return parsed
