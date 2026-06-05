from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("normalized_domain", name="uq_leads_domain"),
        UniqueConstraint("normalized_phone", name="uq_leads_phone"),
        UniqueConstraint("normalized_email", name="uq_leads_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_name: Mapped[str] = mapped_column(String(240), index=True)
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    country: Mapped[str | None] = mapped_column(String(80), index=True)
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(80), default="manual", index=True)
    source_url: Mapped[str | None] = mapped_column(Text)

    website: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(240))
    phone: Mapped[str | None] = mapped_column(String(80))
    whatsapp: Mapped[str | None] = mapped_column(String(80))
    instagram: Mapped[str | None] = mapped_column(String(240))
    linkedin: Mapped[str | None] = mapped_column(String(240))
    address: Mapped[str | None] = mapped_column(Text)

    normalized_domain: Mapped[str | None] = mapped_column(String(240), index=True)
    normalized_email: Mapped[str | None] = mapped_column(String(240), index=True)
    normalized_phone: Mapped[str | None] = mapped_column(String(80), index=True)

    employee_estimate: Mapped[str | None] = mapped_column(String(80))
    branches_estimate: Mapped[int | None] = mapped_column(Integer)
    has_ecommerce: Mapped[bool] = mapped_column(default=False)
    has_mercadolibre: Mapped[bool] = mapped_column(default=False)
    has_whatsapp_commerce: Mapped[bool] = mapped_column(default=False)
    has_physical_store: Mapped[bool] = mapped_column(default=True)
    web_professional: Mapped[bool] = mapped_column(default=False)

    signals_json: Mapped[str] = mapped_column(Text, default="[]")
    score_rules: Mapped[float] = mapped_column(Float, default=0)
    score_ai: Mapped[float | None] = mapped_column(Float)
    fit_score: Mapped[float] = mapped_column(Float, default=0, index=True)
    priority: Mapped[str] = mapped_column(String(1), default="C", index=True)
    ai_reason: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(40), default="new", index=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactEvent(Base):
    __tablename__ = "contact_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(40))
    step: Mapped[str] = mapped_column(String(60))
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
