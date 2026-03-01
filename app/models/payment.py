from __future__ import annotations

from sqlalchemy import ForeignKey, DateTime, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    agent_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    provider_payment_id: Mapped[str | None] = mapped_column(String(255))
    provider_checkout_url: Mapped[str | None] = mapped_column(String(512))
    payment_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))

    agent = relationship("Agent", back_populates="payments")
