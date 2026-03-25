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
    """Retourne le modele Claude par defaut."""
    return os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-20250514")
