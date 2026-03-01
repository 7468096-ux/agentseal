from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CertTest(Base):
    __tablename__ = "cert_tests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    passing_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.6"))
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("5"))
    time_limit_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1800"))
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    cooldown_hours: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("24"))
    max_attempts_per_month: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("3"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    attempts = relationship("CertAttempt", back_populates="test", cascade="all, delete-orphan")


class CertAttempt(Base):
    __tablename__ = "cert_attempts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    agent_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("cert_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    tasks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    answers: Mapped[dict | None] = mapped_column(JSONB)
    results: Mapped[list | None] = mapped_column(JSONB)
    score: Mapped[float | None] = mapped_column(Float)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    seal_issued_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent")
    test = relationship("CertTest", back_populates="attempts")


class CertTask(Base):
    __tablename__ = "cert_tasks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    test_category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    scoring_rubric: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
