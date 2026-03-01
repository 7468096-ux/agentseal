from __future__ import annotations

import re
import secrets
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Agent, AgentSeal, InviteCode, Seal
from app.services.auth_service import create_api_key

PLATFORMS = {"openclaw", "langchain", "autogpt", "crewai", "custom"}
NAME_RE = re.compile(r"^[A-Za-z0-9\-\s]{2,64}$")
SLUG_RE = re.compile(r"^[a-z0-9\-]{2,64}$")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value[:64]


def validate_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
    if meta is None:
        return {}
    if len(str(meta).encode("utf-8")) > 10 * 1024:
        raise HTTPException(status_code=400, detail="metadata too large")
    return meta


def profile_url(slug: str) -> str:
    return f"{settings.app_url}/@{slug}"


async def _consume_invite_code(session: AsyncSession, code: str, agent_id: str) -> None:
    result = await session.execute(select(InviteCode).where(InviteCode.code == code))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=400, detail="invalid invite code")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="invite code expired")
    if invite.max_uses is not None and invite.use_count >= invite.max_uses:
        raise HTTPException(status_code=400, detail="invite code exhausted")
    invite.use_count += 1
    invite.used_by = agent_id
    invite.used_at = datetime.utcnow()


async def _create_invite_codes(session: AsyncSession, agent_id: str, count: int = 3) -> None:
    for _ in range(count):
        code = f"invite_{secrets.token_hex(8)}"
        session.add(InviteCode(code=code, created_by=agent_id, max_uses=1))


async def create_agent(session: AsyncSession, payload: dict[str, Any]) -> tuple[Agent, str]:
    name = payload["name"]
    if not NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="invalid name")

    slug = payload.get("slug") or slugify(name)
    if not SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="invalid slug")

    platform = payload.get("platform") or "custom"
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail="invalid platform")

    meta = validate_metadata(payload.get("metadata"))

    existing = await session.execute(select(Agent).where(Agent.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="slug taken")

    agent = Agent(
        name=name,
        slug=slug,
        description=payload.get("description"),
        platform=platform,
        owner_email=payload.get("owner_email"),
        avatar_url=payload.get("avatar_url"),
        website_url=payload.get("website_url"),
        agent_metadata=meta,
    )
    session.add(agent)
    await session.flush()

    await _consume_invite_code(session, payload["invite_code"], agent.id)

    api_key = await create_api_key(session, agent.id)

    registered_seal = await session.execute(select(Seal).where(Seal.slug == "registered"))
    seal = registered_seal.scalar_one_or_none()
    if seal:
        session.add(AgentSeal(agent_id=agent.id, seal_id=seal.id))

    await _create_invite_codes(session, agent.id, 3)

    return agent, api_key


async def update_agent(session: AsyncSession, agent: Agent, payload: dict[str, Any]) -> Agent:
    if "name" in payload and payload["name"] is not None:
        if not NAME_RE.match(payload["name"]):
            raise HTTPException(status_code=400, detail="invalid name")
        agent.name = payload["name"]

    if "slug" in payload and payload["slug"] is not None:
        slug = payload["slug"]
        if not SLUG_RE.match(slug):
            raise HTTPException(status_code=400, detail="invalid slug")
        existing = await session.execute(select(Agent).where(Agent.slug == slug, Agent.id != agent.id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="slug taken")
        agent.slug = slug

    if "platform" in payload and payload["platform"] is not None:
        if payload["platform"] not in PLATFORMS:
            raise HTTPException(status_code=400, detail="invalid platform")
        agent.platform = payload["platform"]

    for field in ["description", "owner_email", "avatar_url", "website_url"]:
        if field in payload:
            setattr(agent, field, payload[field])

    if "metadata" in payload and payload["metadata"] is not None:
        agent.agent_metadata = validate_metadata(payload["metadata"])

    return agent


async def get_agent_by_id(session: AsyncSession, agent_id: str) -> Agent | None:
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def get_agent_by_slug(session: AsyncSession, slug: str) -> Agent | None:
    result = await session.execute(select(Agent).where(Agent.slug == slug))
    return result.scalar_one_or_none()
