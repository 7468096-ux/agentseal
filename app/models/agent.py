from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, server_default="custom", index=True)
    owner_email: Mapped[str | None] = mapped_column(String(255))
    owner_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    website_url: Mapped[str | None] = mapped_column(String(512))
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True, server_default=text("false"))
    trust_score: Mapped[float | None] = mapped_column(Float)
    trust_tier: Mapped[str | None] = mapped_column(String(20))
    agent_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("ApiKey", back_populates="agent", cascade="all, delete-orphan")
    seals = relationship("AgentSeal", back_populates="agent", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="agent", cascade="all, delete-orphan")
    behaviour_reports_received = relationship(
        "BehaviourReport",
        foreign_keys="BehaviourReport.subject_agent_id",
        cascade="all, delete-orphan",
    )
    behaviour_reports_sent = relationship(
        "BehaviourReport",
        foreign_keys="BehaviourReport.reporter_agent_id",
    )
    invite_codes_created = relationship(
        "InviteCode",
        back_populates="created_by_agent",
        foreign_keys="InviteCode.created_by",
    )
    invite_codes_used = relationship(
        "InviteCode",
        back_populates="used_by_agent",
        foreign_keys="InviteCode.used_by",
    )
    claim_requests = relationship("ClaimRequest", back_populates="agent", cascade="all, delete-orphan")
