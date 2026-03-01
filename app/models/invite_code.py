from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    used_by: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    used_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[int | None] = mapped_column(Integer)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    created_by_agent = relationship("Agent", back_populates="invite_codes_created", foreign_keys=[created_by])
    used_by_agent = relationship("Agent", back_populates="invite_codes_used", foreign_keys=[used_by])
