"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=False, server_default="custom"),
        sa.Column("owner_email", sa.String(length=255), nullable=True),
        sa.Column("owner_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_agents_slug", "agents", ["slug"], unique=False)
    op.create_index("idx_agents_platform", "agents", ["platform"], unique=False)
    op.create_index("idx_agents_created", "agents", ["created_at"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("key_prefix", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_api_keys_agent", "api_keys", ["agent_id"], unique=False)
    op.create_index("idx_api_keys_prefix", "api_keys", ["key_prefix"], unique=False)

    op.create_table(
        "seals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("tier", sa.String(length=10), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("icon_emoji", sa.String(length=10), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("max_supply", sa.Integer(), nullable=True),
        sa.Column("issued_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requirements", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_seals_category", "seals", ["category"], unique=False)
    op.create_index("idx_seals_slug", "seals", ["slug"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="stripe"),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("provider_checkout_url", sa.String(length=512), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_payments_agent", "payments", ["agent_id"], unique=False)
    op.create_index("idx_payments_status", "payments", ["status"], unique=False)
    op.create_index("idx_payments_provider_id", "payments", ["provider_payment_id"], unique=False)

    op.create_table(
        "agent_seals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof", postgresql.JSONB(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=255), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seal_id"], ["seals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.UniqueConstraint("agent_id", "seal_id", name="uq_agent_seal"),
    )
    op.create_index("idx_agent_seals_agent", "agent_seals", ["agent_id"], unique=False)
    op.create_index("idx_agent_seals_seal", "agent_seals", ["seal_id"], unique=False)

    op.create_table(
        "invite_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("used_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by"], ["agents.id"]),
    )
    op.create_index("idx_invite_codes_code", "invite_codes", ["code"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_invite_codes_code", table_name="invite_codes")
    op.drop_table("invite_codes")
    op.drop_index("idx_agent_seals_seal", table_name="agent_seals")
    op.drop_index("idx_agent_seals_agent", table_name="agent_seals")
    op.drop_table("agent_seals")
    op.drop_index("idx_payments_provider_id", table_name="payments")
    op.drop_index("idx_payments_status", table_name="payments")
    op.drop_index("idx_payments_agent", table_name="payments")
    op.drop_table("payments")
    op.drop_index("idx_seals_slug", table_name="seals")
    op.drop_index("idx_seals_category", table_name="seals")
    op.drop_table("seals")
    op.drop_index("idx_api_keys_prefix", table_name="api_keys")
    op.drop_index("idx_api_keys_agent", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index("idx_agents_created", table_name="agents")
    op.drop_index("idx_agents_platform", table_name="agents")
    op.drop_index("idx_agents_slug", table_name="agents")
    op.drop_table("agents")
