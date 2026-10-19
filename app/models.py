"""Modelo relacional: usuarios y evidencias con su cadena de custodia."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    evidences: Mapped[list["Evidence"]] = relationship(back_populates="owner")


class Evidence(Base):
    """Un fichero custodiado: su huella SHA-256 y el momento en que se registró."""

    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    owner: Mapped[User] = relationship(back_populates="evidences")
    events: Mapped[list["CustodyEvent"]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan", order_by="CustodyEvent.at"
    )


class CustodyEvent(Base):
    """Cada acción sobre una evidencia queda registrada: quién, qué y cuándo."""

    __tablename__ = "custody_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidences.id"), index=True, nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # registered, verified, summarized...
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    evidence: Mapped[Evidence] = relationship(back_populates="events")
