"""
Analyseur de use cases Braze -- appel Claude + parsing JSON.
Porte depuis braze_data_model/agent.py.
"""
import json
import logging
import os
import re

from services.data_model.reference import get_data_model_prompt
from services.data_model.demo_data import DEMO_RESULTS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un expert Braze, specialise dans le data model et l'architecture de donnees CRM/Marketing Automation.

{data_model}

# Ton role

A partir de use cases metiers fournis par l'utilisateur, tu dois:

1. **Analyser chaque use case** et identifier les objets/entites Braze necessaires
2. **Lister les donnees requises** avec:
   - Les entites Braze concernees (User Profile, Custom Events, Purchases, Segments, Campaigns, Canvas, etc.)
   - Les attributs specifiques necessaires pour chaque entite
   - Les custom attributes et custom events a creer
   - Les segments a definir
3. **Produire la hierarchie du data model** filtree pour ce use case
4. **Estimer l'impact en Data Points** pour chaque attribut et evenement

# Format de reponse

Tu DOIS repondre UNIQUEMENT avec un JSON valide (pas de texte avant ou apres) au format suivant:

{{
  "use_case_analysis": [
    {{
      "use_case": "Description du use case",
      "description": "Explication detaillee de l'implementation Braze",
      "required_data": [
        {{
          "entity": "Nom de l'entite Braze",
          "attributes": ["liste", "des", "attributs", "necessaires"],
          "custom_fields": [
            {{
              "name": "nom_du_champ",
              "type": "string|integer|float|boolean|date|array",
              "description": "Description du champ",
              "update_frequency": "once|daily|weekly|monthly|per_occurrence",
              "avg_monthly_occurrences": 2
            }}
          ],
          "purpose": "Pourquoi cette entite est necessaire pour le use case"
        }}
      ],
      "segments": [
        {{
          "name": "Nom du segment",
          "filters": ["Description des filtres"]
        }}
      ],
      "messaging": {{
        "channels": ["email", "push", "sms", "in_app_message", "content_card"],
        "trigger_type": "scheduled|action_based|api_triggered",
        "trigger_details": "Details du declenchement"
      }}
    }}
  ],
  "data_hierarchy": [...],
  "mermaid_diagram": "graph TD\\n  A[Entity1] --> B[Entity2]\\n  ...",
  "data_points_optimization": [
    "Liste de suggestions pour reduire la consommation de data points",
    "Ex: Utiliser event properties au lieu de custom attributes pour les donnees volatiles"
  ]
}}

# Regles pour les champs custom_fields

Pour CHAQUE custom_field, tu DOIS indiquer:
- **update_frequency**: la frequence estimee de mise a jour de cet attribut:
  - "once" : ecrit une seule fois (ex: date d'inscription, source d'acquisition)
  - "daily" : mis a jour quotidiennement (ex: score d'engagement, derniere activite)
  - "weekly" : mis a jour hebdomadairement (ex: panier en cours, preferences)
  - "monthly" : mis a jour mensuellement (ex: palier fidelite, segment)
  - "per_occurrence" : mis a jour a chaque occurrence d'un evenement
- **avg_monthly_occurrences** (uniquement pour les Custom Events) : nombre moyen d'occurrences par utilisateur et par mois (ex: 2 pour un achat, 10 pour un ajout au panier)

# Section data_points_optimization

Ajoute une liste de recommandations concretes pour optimiser la consommation de data points:
- Attributs qui pourraient etre remplaces par des event properties
- Donnees de reference qui devraient etre dans un Catalog ou Connected Content
- Attributs avec une frequence de mise a jour trop elevee

IMPORTANT - Optimisation des Data Points Braze :
- Chaque mise a jour de custom attribute, custom event, et purchase consomme des data points
- Les attributs standard (email, first_name, last_name, country, home_city, language, gender, phone_number, date_of_birth, time_zone) sont GRATUITS
- Les event properties ne consomment PAS de data points
- Prefere les event properties aux custom attributes pour les donnees volatiles
- Limite : 250 custom attributes et 250 custom events max par app group
- Recommande Connected Content ou Catalogs pour les donnees de reference
- Indique systematiquement si tu recommandes un Canvas ou une Campaign, et pourquoi

IMPORTANT:
- Reponds UNIQUEMENT avec le JSON, sans texte additionnel
- Le diagramme Mermaid doit representer la hierarchie des entites utilisees
"""


def analyze_use_cases(use_cases: list[str], model: str | None = None) -> dict:
    """Analyse une liste de use cases via Claude et retourne le JSON structure.

    Si ANTHROPIC_API_KEY n'est pas definie, bascule automatiquement en mode demo.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("Pas de cle API Anthropic -- mode demo (data model analyzer)")
        return DEMO_RESULTS

    from services.claude_client import get_claude_client, get_default_model

    client = get_claude_client()
    model = model or get_default_model()

    data_model_text = get_data_model_prompt()
    system = SYSTEM_PROMPT.format(data_model=data_model_text)

    user_message = "Voici les use cases metiers a analyser:\n\n"
    for i, uc in enumerate(use_cases, 1):
        user_message += f"{i}. {uc}\n"
    user_message += "\nAnalyse chaque use case et fournis le JSON structure avec les donnees necessaires et la hierarchie."

    response = client.messages.create(
        model=model,
        max_tokens=16384,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Nettoyer le JSON si entoure de ```json ... ```
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw_text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {
            "error": "L'agent n'a pas retourne un JSON valide",
            "raw_response": raw_text,
        }


def analyze_use_cases_demo() -> dict:
    """Retourne les resultats de demonstration sans appel API."""
    return DEMO_RESULTS


def format_results_text(results: dict) -> str:
    """Formate les resultats en texte lisible."""
    if "error" in results:
        return f"Erreur: {results['error']}\n\nReponse brute:\n{results.get('raw_response', 'N/A')}"

    lines = []
    for analysis in results.get("use_case_analysis", []):
        lines.append(f"{'=' * 60}")
        lines.append(f"USE CASE: {analysis.get('use_case', 'Sans titre')}")
        lines.append(f"{'=' * 60}")
        lines.append(f"\n{analysis.get('description', '')}\n")
        lines.append("DONNEES REQUISES:")
        lines.append("-" * 40)
        for data in analysis.get("required_data", []):
            lines.append(f"\n  Entite: {data.get('entity', 'Entite')}")
            lines.append(f"  Objectif: {data.get('purpose', '')}")
            if data.get("attributes"):
                lines.append(f"  Attributs: {', '.join(data['attributes'])}")
            if data.get("custom_fields"):
                lines.append("  Champs custom:")
                for field in data["custom_fields"]:
                    lines.append(f"    - {field['name']} ({field['type']}): {field.get('description', '')}")
        lines.append("")
    return "\n".join(lines)


def extract_mermaid(results: dict) -> str:
    """Extrait le diagramme Mermaid des resultats."""
    if "error" in results:
        return "graph TD\n  Error[Erreur de generation]"
    return results.get("mermaid_diagram", "graph TD\n  A[Pas de diagramme genere]")
