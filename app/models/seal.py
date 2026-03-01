from __future__ import annotations

from sqlalchemy import ForeignKey, Boolean, DateTime, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Seal(Base):
    __tablename__ = "seals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    tier: Mapped[str | None] = mapped_column(String(10))
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    icon_emoji: Mapped[str | None] = mapped_column(String(10))
    color: Mapped[str | None] = mapped_column(String(7))
    max_supply: Mapped[int | None] = mapped_column(Integer)
    issued_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent_seals = relationship("AgentSeal", back_populates="seal")


class AgentSeal(Base):
    __tablename__ = "agent_seals"
    __table_args__ = (UniqueConstraint("agent_id", "seal_id", name="uq_agent_seal"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    agent_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    seal_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("seals.id", ondelete="RESTRICT"), nullable=False, index=True)
    issued_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    proof: Mapped[dict | None] = mapped_column(JSONB)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    revoked_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(String(255))
    payment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True))

    agent = relationship("Agent", back_populates="seals")
    seal = relationship("Seal", back_populates="agent_seals")
