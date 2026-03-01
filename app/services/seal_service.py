from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Agent, AgentSeal, Seal
from app.services.payment_service import create_payment_stub
from app.services.trust_service import recalculate_trust_score


def price_display(cents: int) -> str:
    return f"${cents/100:.2f}"


def is_available(seal: Seal) -> bool:
    if not seal.is_active:
        return False
    if seal.max_supply is not None and seal.issued_count >= seal.max_supply:
        return False
    return True


async def list_seals(session: AsyncSession, category: str | None, limit: int, offset: int) -> tuple[list[Seal], int]:
    query = select(Seal)
    if category:
        query = query.where(Seal.category == category)
    total = await session.execute(select(func.count()).select_from(query.subquery()))
    total_count = total.scalar_one()
    result = await session.execute(query.offset(offset).limit(limit))
    return result.scalars().all(), total_count


async def get_seal(session: AsyncSession, seal_id: str) -> Seal | None:
    result = await session.execute(select(Seal).where(Seal.id == seal_id))
    return result.scalar_one_or_none()


async def get_seal_by_slug(session: AsyncSession, slug: str) -> Seal | None:
    result = await session.execute(select(Seal).where(Seal.slug == slug))
    return result.scalar_one_or_none()


async def issue_seal(session: AsyncSession, agent: Agent, seal_slug: str) -> dict:
    seal = await get_seal_by_slug(session, seal_slug)
    if not seal:
        raise HTTPException(status_code=404, detail="seal not found")
    if not is_available(seal):
        raise HTTPException(status_code=410, detail="seal supply exhausted")

    if seal.category == "earned":
        raise HTTPException(status_code=403, detail="earned seals cannot be purchased")
    if seal.category == "certification":
        raise HTTPException(status_code=403, detail="certification seals cannot be purchased")

    existing = await session.execute(
        select(AgentSeal).where(AgentSeal.agent_id == agent.id, AgentSeal.seal_id == seal.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="already has this seal")

    if seal.price_cents == 0:
        agent_seal = AgentSeal(agent_id=agent.id, seal_id=seal.id)
        session.add(agent_seal)
        seal.issued_count += 1
        await recalculate_trust_score(session, agent)
        return {
            "type": "free",
            "agent_seal": agent_seal,
            "seal": seal,
        }

    payment = await create_payment_stub(session, agent, seal)
    return {
        "type": "paid",
        "payment": payment,
        "checkout_url": payment.provider_checkout_url,
        "expires_in_seconds": 1800,
    }


async def list_agent_seals(session: AsyncSession, agent_id: str) -> list[AgentSeal]:
    result = await session.execute(
        select(AgentSeal)
        .where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
        )
        .order_by(AgentSeal.issued_at.desc())
    )
    return result.scalars().all()
