"""Database configuration -- Neon PostgreSQL via SQLAlchemy."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jbraze_dev.db")

# Valider que c'est une vraie URL de BDD (pas une valeur parasite)
_url = DATABASE_URL
if not any(_url.startswith(p) for p in ("sqlite", "postgres", "postgresql", "mysql")):
    # Valeur invalide (ex: "braze") — fallback SQLite dans /tmp (writable en serverless)
    _url = "sqlite:////tmp/jbraze_dev.db"

# En serverless, /var/task est read-only — utiliser /tmp pour SQLite
if _url.startswith("sqlite:///./"):
    import pathlib
    # Si le répertoire courant n'est pas writable, utiliser /tmp
    cwd = pathlib.Path.cwd()
    if not os.access(str(cwd), os.W_OK):
        _url = "sqlite:////tmp/jbraze_dev.db"

# Neon PostgreSQL : convertir postgres:// en postgresql+pg8000://
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql+pg8000://", 1)
elif _url.startswith("postgresql://") and "+pg8000" not in _url:
    _url = _url.replace("postgresql://", "postgresql+pg8000://", 1)

connect_args = {}
if _url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "pg8000" in _url:
    # pg8000 gere SSL automatiquement avec Neon
    connect_args = {}

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
