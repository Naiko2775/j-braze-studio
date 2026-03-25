"""Modeles Pydantic pour les donnees de migration (normalises)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContactAttribute(BaseModel):
    key: str
    value: Any
    type: str = "string"


class Contact(BaseModel):
    external_id: str
    email: str | None = None
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language: str | None = None
    country: str | None = None
    city: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    email_subscribe: str = "subscribed"
    push_subscribe: str = "subscribed"
    custom_attributes: list[ContactAttribute] = Field(default_factory=list)
    segment_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source_id: str | None = None
    source_platform: str | None = None


class CustomEvent(BaseModel):
    external_id: str
    name: str
    time: datetime
    properties: dict[str, Any] = Field(default_factory=dict)
    source_id: str | None = None
    source_platform: str | None = None


class Segment(BaseModel):
    id: str
    name: str
    description: str | None = None
    contact_ids: list[str] = Field(default_factory=list)
    source_id: str | None = None
    source_platform: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EmailTemplate(BaseModel):
    id: str
    name: str
    subject: str | None = None
    html_body: str | None = None
    text_body: str | None = None
    from_name: str | None = None
    from_email: str | None = None
    reply_to: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_id: str | None = None
    source_platform: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
