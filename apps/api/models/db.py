"""Database configuration -- Neon PostgreSQL via SQLAlchemy."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jbraze_dev.db")

# Neon PostgreSQL : convertir postgres:// en postgresql+pg8000://
_url = DATABASE_URL
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


def get_db():
    """Dependency FastAPI pour obtenir une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
