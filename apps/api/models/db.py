"""Database configuration -- Neon PostgreSQL via SQLAlchemy."""
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

_EPHEMERAL_SQLITE = "sqlite:////tmp/jbraze_dev.db"
# Parametres compris par libpq/psycopg2 mais refuses par pg8000 : les laisser
# dans l'URL provoque un TypeError des la premiere connexion. Neon les inclut
# systematiquement dans ses chaines de connexion.
_LIBPQ_ONLY_PARAMS = ("sslmode", "channel_binding")


def _strip_libpq_params(url: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(url)
    if not parts.query:
        return url
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    kept = [(k, v) for k, v in pairs if k not in _LIBPQ_ONLY_PARAMS]
    dropped = [k for k, _ in pairs if k in _LIBPQ_ONLY_PARAMS]
    if dropped:
        logger.info(
            "Parametres ignores par pg8000 et retires de l'URL: %s "
            "(TLS assure par ssl_context).",
            ", ".join(dropped),
        )
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment)
    )

_VALID_PREFIXES = ("sqlite", "postgres", "postgresql", "mysql")


def normalize_database_url(raw: str | None) -> str:
    """Valide et normalise DATABASE_URL.

    Source unique partagee avec alembic/env.py : les migrations et l'app
    doivent viser exactement la meme base, avec le meme driver.
    Tout repli sur SQLite ephemere est journalise bruyamment -- un repli
    silencieux transforme une mauvaise config en perte de donnees invisible.
    """
    url = (raw or "").strip() or "sqlite:///./jbraze_dev.db"

    if not any(url.startswith(p) for p in _VALID_PREFIXES):
        # Valeur parasite (ex: "braze") : on ne loggue que le schema, jamais
        # l'URL complete, qui contient les identifiants.
        logger.error(
            "DATABASE_URL invalide (schema=%r) -- repli sur SQLite ephemere.",
            url.split("://")[0][:30],
        )
        url = _EPHEMERAL_SQLITE

    # En serverless, /var/task est read-only -- basculer SQLite vers /tmp
    if url.startswith("sqlite:///./"):
        import pathlib

        if not os.access(str(pathlib.Path.cwd()), os.W_OK):
            url = _EPHEMERAL_SQLITE

    if url == _EPHEMERAL_SQLITE:
        logger.warning(
            "Base SQLite ephemere dans /tmp : chaque instance serverless part "
            "d'une base vide et les donnees sont perdues a chaque demarrage a "
            "froid. Definir DATABASE_URL vers Neon PostgreSQL."
        )

    # Neon PostgreSQL : pg8000 est le seul driver installe (cf. requirements.txt)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql://") and "+pg8000" not in url:
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)

    if "+pg8000" in url:
        url = _strip_libpq_params(url)

    return url


DATABASE_URL = os.getenv("DATABASE_URL")
_url = normalize_database_url(DATABASE_URL)

def build_connect_args(url: str) -> dict:
    """Arguments de connexion SQLAlchemy, partages avec alembic/env.py.

    Les migrations et l'application doivent viser la meme base avec les
    memes garanties TLS.
    """
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    if "pg8000" in url:
        # Sans ssl_context explicite, pg8000 chiffre mais ne verifie NI le nom
        # d'hote NI le certificat (cf. pg8000/core.py : check_hostname=False,
        # verify_mode=CERT_NONE). On fournit un contexte verifiant.
        import ssl

        return {"ssl_context": ssl.create_default_context()}
    return {}


connect_args = build_connect_args(_url)

engine = create_engine(_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


_tables_created = False


def ensure_tables():
    """Crée les tables si elles n'existent pas (SQLite serverless)."""
    global _tables_created
    if _tables_created:
        return
    if _url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    _tables_created = True


def get_db():
    """Dependency FastAPI pour obtenir une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
