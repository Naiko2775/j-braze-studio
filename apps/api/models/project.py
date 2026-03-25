"""Modele SQLAlchemy pour les projets clients."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from models.db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    client_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    braze_instance = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
