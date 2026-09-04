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


def _is_db_url(value: str | None) -> bool:
    return bool(value) and any(value.startswith(p) for p in _VALID_PREFIXES)


def resolve_database_url() -> tuple[str | None, str]:
    """Trouve l'URL de base dans l'environnement, prefixe compris.

    L'integration Vercel-Neon peut prefixer toutes ses variables (ici
    "braze_"), si bien que la chaine reelle vit dans braze_DATABASE_URL et non
    dans DATABASE_URL. C'est exactement cette confusion prefixe/valeur qui a
    fait tomber l'application sur du SQLite ephemere.

    Un DATABASE_URL explicite et valide gagne toujours. Sinon on retient la
    premiere variable valide se terminant par _DATABASE_URL, puis
    _POSTGRES_URL -- jamais _POSTGRES_URL_NO_SSL, dont le suffixe ne
    correspond pas, ce qui evite de degrader la connexion en clair.

    Retourne (url, nom_de_la_variable) pour journaliser la source sans jamais
    exposer la valeur.
    """
    explicit = os.getenv("DATABASE_URL")
    if _is_db_url(explicit):
        return explicit, "DATABASE_URL"

    for suffix in ("_DATABASE_URL", "_POSTGRES_URL"):
        for key in sorted(os.environ):
            if key.endswith(suffix) and _is_db_url(os.environ[key]):
                return os.environ[key], key

    return explicit, "DATABASE_URL"


DATABASE_URL, _source_var = resolve_database_url()
if _source_var != "DATABASE_URL":
    logger.warning(
        "DATABASE_URL absente ou invalide : utilisation de %s, fournie par "
        "l'integration. Corriger ou supprimer DATABASE_URL pour lever "
        "l'ambiguite.",
        _source_var,
    )
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
    """Cree les tables si elles n'existent pas (SQLite serverless).

    Appelee a l'import de `models` : en serverless, Mangum tourne avec
    lifespan="off", donc les handlers de startup FastAPI ne s'executent pas.

    Sous Alembic, ce raccourci doit rester inerte : create_all() creerait le
    schema avant que les migrations ne tournent, et `upgrade head` echouerait
    sur "table already exists". Les migrations sont la source de verite du
    schema ; ce helper n'est qu'un filet pour le SQLite ephemere.
    """
    global _tables_created
    if os.getenv("JBRAZE_SKIP_AUTO_CREATE"):
        return
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
