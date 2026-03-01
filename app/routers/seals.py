from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Agent, AgentSeal, Seal
from app.schemas.seal import (
    AgentSealsResponse,
    IssueSealPaidResponse,
    IssueSealFreeResponse,
    IssueSealRequest,
    SealDetailAgent,
    SealDetailResponse,
    SealListResponse,
    SealResponse,
)
from app.services.agent_service import get_agent_by_id, profile_url
from app.services.seal_service import is_available, issue_seal, list_agent_seals, list_seals, price_display, get_seal

router = APIRouter(prefix="/v1", tags=["seals"])


@router.get("/seals", response_model=SealListResponse)
async def list_seals_endpoint(
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    limit = min(limit, 100)
    seals, total = await list_seals(session, category, limit, offset)
    response = [
        SealResponse(
            id=str(seal.id),
            name=seal.name,
            slug=seal.slug,
            description=seal.description,
            category=seal.category,
            tier=seal.tier,
            price_cents=seal.price_cents,
            price_display=price_display(seal.price_cents),
            icon_emoji=seal.icon_emoji,
            color=seal.color,
            max_supply=seal.max_supply,
            issued_count=seal.issued_count,
            available=is_available(seal),
        )
        for seal in seals
    ]
    return SealListResponse(seals=response, total=total, limit=limit, offset=offset)


@router.get("/seals/{seal_id}", response_model=SealDetailResponse)
async def seal_detail(seal_id: str, session: AsyncSession = Depends(get_session)):
    seal = await get_seal(session, seal_id)
    if not seal:
        raise HTTPException(status_code=404, detail="seal not found")

    recent = await session.execute(
        select(Agent)
        .join(AgentSeal, AgentSeal.agent_id == Agent.id)
        .where(
            AgentSeal.seal_id == seal.id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
        )
        .order_by(AgentSeal.issued_at.desc())
        .limit(10)
    )
    agents = recent.scalars().all()
    recent_agents = [
        SealDetailAgent(id=str(agent.id), name=agent.name, slug=agent.slug, profile_url=profile_url(agent.slug))
        for agent in agents
    ]

    return SealDetailResponse(
        id=str(seal.id),
        name=seal.name,
        slug=seal.slug,
        description=seal.description,
        category=seal.category,
        tier=seal.tier,
        price_cents=seal.price_cents,
        price_display=price_display(seal.price_cents),
        icon_emoji=seal.icon_emoji,
        color=seal.color,
        max_supply=seal.max_supply,
        issued_count=seal.issued_count,
        is_active=seal.is_active,
        requirements=seal.requirements,
        created_at=seal.created_at,
        recent_agents=recent_agents,
    )


@router.post("/agents/{agent_id}/seals", response_model=IssueSealFreeResponse | IssueSealPaidResponse, status_code=201)
async def issue_seal_endpoint(
    agent_id: str,
    payload: IssueSealRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    if str(agent.id) != getattr(request.state, "agent_id", None):
        raise HTTPException(status_code=403, detail="forbidden")

    result = await issue_seal(session, agent, payload.seal_slug)
    await session.commit()

    if result["type"] == "free":
        agent_seal = result["agent_seal"]
        seal = result["seal"]
        return IssueSealFreeResponse(
            agent_seal={
                "id": str(agent_seal.id),
                "seal": {
                    "id": str(seal.id),
                    "name": seal.name,
                    "slug": seal.slug,
                    "category": seal.category,
                    "tier": seal.tier,
                    "icon_emoji": seal.icon_emoji,
                    "color": seal.color,
                },
                "issued_at": agent_seal.issued_at,
                "expires_at": agent_seal.expires_at,
            }
        )

    if response is not None:
        response.status_code = 202
    return IssueSealPaidResponse(
        payment_required=True,
        checkout_url=result["checkout_url"],
        payment_id=str(result["payment"].id),
        expires_in_seconds=result["expires_in_seconds"],
    )


@router.get("/agents/{agent_id}/seals", response_model=AgentSealsResponse)
async def agent_seals(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    agent_seals = await list_agent_seals(session, agent.id)
    if not agent_seals:
        return AgentSealsResponse(seals=[], count=0)

    seal_ids = [s.seal_id for s in agent_seals]
    seals_result = await session.execute(select(Seal).where(Seal.id.in_(seal_ids)))
    seals = {str(seal.id): seal for seal in seals_result.scalars().all()}

    response = []
    for agent_seal in agent_seals:
        seal = seals.get(str(agent_seal.seal_id))
        if not seal:
            continue
        response.append(
            {
                "seal_name": seal.name,
                "seal_slug": seal.slug,
                "category": seal.category,
                "icon_emoji": seal.icon_emoji,
                "issued_at": agent_seal.issued_at,
                "expires_at": agent_seal.expires_at,
                "revoked": agent_seal.revoked,
            }
        )

    return AgentSealsResponse(seals=response, count=len(response))


@router.delete("/agents/{agent_id}/seals/{seal_id}", status_code=204)
async def revoke_seal(agent_id: str, seal_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    if str(agent.id) != getattr(request.state, "agent_id", None):
        raise HTTPException(status_code=403, detail="forbidden")

    result = await session.execute(
        select(AgentSeal).where(AgentSeal.agent_id == agent.id, AgentSeal.seal_id == seal_id)
    )
    agent_seal = result.scalar_one_or_none()
    if not agent_seal:
        raise HTTPException(status_code=404, detail="seal not found")

    agent_seal.revoked = True
    from datetime import datetime
    agent_seal.revoked_at = datetime.utcnow()
    await session.commit()
    return None
