from __future__ import annotations

from sqlalchemy import DateTime, Float, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BehaviourReport(Base):
    __tablename__ = "behaviour_reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    subject_agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), index=True
    )
    reporter_type: Mapped[str] = mapped_column(String(20), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB)
    weight: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("1.0"))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    subject_agent = relationship("Agent", foreign_keys=[subject_agent_id])
    reporter_agent = relationship("Agent", foreign_keys=[reporter_agent_id])
