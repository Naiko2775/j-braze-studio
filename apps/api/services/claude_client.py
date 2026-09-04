"""Client Anthropic partage -- centralise la cle API cote serveur."""
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Cle API runtime (settable via l'UI Parametres)
_runtime_api_key: str | None = None


def set_runtime_api_key(key: str) -> None:
    """Definit la cle API Claude depuis l'UI (stockee en memoire serveur)."""
    global _runtime_api_key
    _runtime_api_key = key if key else None
    # Met aussi a jour os.environ pour que les health checks la detectent
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
    elif "ANTHROPIC_API_KEY" in os.environ and os.environ["ANTHROPIC_API_KEY"] == _runtime_api_key:
        del os.environ["ANTHROPIC_API_KEY"]


def get_api_key() -> str | None:
    """Retourne la cle API Claude (runtime > env var)."""
    return _runtime_api_key or os.getenv("ANTHROPIC_API_KEY")


def get_claude_client() -> anthropic.Anthropic:
    """Cree et retourne le client Anthropic avec la cle serveur."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY non definie. "
            "Renseignez-la dans Parametres ou dans les variables d'environnement."
        )
    return anthropic.Anthropic(api_key=api_key)


def get_default_model() -> str:
    """Retourne le modele Claude par defaut (generation Liquid)."""
    return os.getenv("CLAUDE_DEFAULT_MODEL", "claude-opus-5")


def get_analysis_model() -> str:
    """Modele du module Data Model.

    Opus 5 par defaut : sur un use case reel (relance panier abandonne, 8057
    tokens d'entree) il produit l'analyse la plus riche et la plus reguliere
    -- 16 entites, 73 attributs -- la ou Haiku 4.5 varie de 5 a 12 champs
    d'un appel a l'autre et ne cite Catalog qu'une fois sur trois.

    Le compromis est la latence : ~109s contre ~34-52s pour Haiku 4.5
    ($0.288 contre $0.026 par analyse). Pour une demo ou la reactivite prime
    sur la profondeur, definir sans redeploiement :
        CLAUDE_ANALYSIS_MODEL=claude-haiku-4-5
    """
    return os.getenv("CLAUDE_ANALYSIS_MODEL", "claude-opus-5")
