from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import AgentSeal, Seal
from app.schemas.agent import (
    AgentCardResponse,
    AgentCreate,
    AgentCreateResponse,
    AgentProfileResponse,
    AgentResponse,
    AgentUpdate,
    AgentSealSummary,
)
from app.schemas.trust import TrustScoreResponse
from app.services.agent_service import create_agent, get_agent_by_id, get_agent_by_slug, profile_url, update_agent
from app.services.trust_service import compute_trust_breakdown

router = APIRouter(prefix="/v1/agents", tags=["agents"])


def build_seal_summary(agent_seals: list[AgentSeal], seals_by_id: dict[str, Seal]) -> list[AgentSealSummary]:
    summaries: list[AgentSealSummary] = []
    for agent_seal in agent_seals:
        seal = seals_by_id.get(str(agent_seal.seal_id))
        if not seal:
            continue
        summaries.append(
            AgentSealSummary(
                id=str(seal.id),
                seal_name=seal.name,
                seal_slug=seal.slug,
                category=seal.category,
                tier=seal.tier,
                icon_emoji=seal.icon_emoji,
                color=seal.color,
                issued_at=agent_seal.issued_at,
                expires_at=agent_seal.expires_at,
            )
        )
    return summaries


async def get_agent_seals(session: AsyncSession, agent_id: str) -> tuple[list[AgentSeal], dict[str, Seal]]:
    result = await session.execute(
        select(AgentSeal).where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
        )
    )
    agent_seals = result.scalars().all()
    if not agent_seals:
        return [], {}
    seal_ids = [s.seal_id for s in agent_seals]
    seals_result = await session.execute(select(Seal).where(Seal.id.in_(seal_ids)))
    seals = seals_result.scalars().all()
    return agent_seals, {str(seal.id): seal for seal in seals}


@router.post("", response_model=AgentCreateResponse, status_code=201)
async def register_agent(payload: AgentCreate, session: AsyncSession = Depends(get_session)):
    agent, api_key = await create_agent(session, payload.model_dump(exclude_none=True))
    await session.commit()

    agent_seals, seals_by_id = await get_agent_seals(session, agent.id)
    seals = build_seal_summary(agent_seals, seals_by_id)

    response = AgentResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        platform=agent.platform,
        owner_verified=agent.owner_verified,
        avatar_url=agent.avatar_url,
        website_url=agent.website_url,
        metadata=agent.agent_metadata,
        seals=seals,
        created_at=agent.created_at,
        profile_url=profile_url(agent.slug),
    )
    return AgentCreateResponse(agent=response, api_key=api_key, warning="Save this API key — it will not be shown again.")


@router.get("/{agent_id}", response_model=AgentProfileResponse)
async def get_agent(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    agent_seals, seals_by_id = await get_agent_seals(session, agent.id)
    seals = build_seal_summary(agent_seals, seals_by_id)

    return AgentProfileResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        platform=agent.platform,
        owner_verified=agent.owner_verified,
        avatar_url=agent.avatar_url,
        website_url=agent.website_url,
        metadata=agent.agent_metadata,
        seals=seals,
        seal_count=len(seals),
        created_at=agent.created_at,
        profile_url=profile_url(agent.slug),
    )


@router.get("/by-slug/{slug}", response_model=AgentProfileResponse)
async def get_agent_by_slug_endpoint(slug: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_slug(session, slug)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    agent_seals, seals_by_id = await get_agent_seals(session, agent.id)
    seals = build_seal_summary(agent_seals, seals_by_id)

    return AgentProfileResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        platform=agent.platform,
        owner_verified=agent.owner_verified,
        avatar_url=agent.avatar_url,
        website_url=agent.website_url,
        metadata=agent.agent_metadata,
        seals=seals,
        seal_count=len(seals),
        created_at=agent.created_at,
        profile_url=profile_url(agent.slug),
    )


@router.patch("/{agent_id}", response_model=AgentProfileResponse)
async def update_agent_endpoint(
    agent_id: str,
    payload: AgentUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    if str(agent.id) != getattr(request.state, "agent_id", None):
        raise HTTPException(status_code=403, detail="forbidden")

    agent = await update_agent(session, agent, payload.model_dump(exclude_none=True))
    await session.commit()

    agent_seals, seals_by_id = await get_agent_seals(session, agent.id)
    seals = build_seal_summary(agent_seals, seals_by_id)

    return AgentProfileResponse(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        platform=agent.platform,
        owner_verified=agent.owner_verified,
        avatar_url=agent.avatar_url,
        website_url=agent.website_url,
        metadata=agent.agent_metadata,
        seals=seals,
        seal_count=len(seals),
        created_at=agent.created_at,
        profile_url=profile_url(agent.slug),
    )


@router.get("/{agent_id}/card", response_model=AgentCardResponse)
async def agent_card(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    agent_seals, seals_by_id = await get_agent_seals(session, agent.id)
    seal_slugs = [seals_by_id[str(s.seal_id)].slug for s in agent_seals if str(s.seal_id) in seals_by_id]

    return AgentCardResponse(
        name=agent.name,
        description=agent.description,
        url=profile_url(agent.slug),
        provider={"organization": "AgentSeal", "url": "https://agentseal.io"},
        version="1.0",
        capabilities={"seals": seal_slugs, "trust_score": None},
        authentication={"schemes": ["apiKey"]},
    )


def _text_width(text: str, padding: int = 12) -> int:
    return max(40, len(text) * 6 + padding)


def _build_badge_svg(label: str, value: str, color: str) -> str:
    left_width = _text_width(label)
    right_width = _text_width(value)
    total_width = left_width + right_width
    height = 20
    font_family = "Verdana,DejaVu Sans,sans-serif"
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{total_width}' height='{height}' role='img'"
        f" aria-label='{label}: {value}'>"
        f"<rect width='{total_width}' height='{height}' rx='3' fill='#2f3641'/>"
        f"<rect x='{left_width}' width='{right_width}' height='{height}' rx='3' fill='{color}'/>"
        f"<text x='{left_width / 2}' y='14' fill='#fff' font-family='{font_family}' font-size='11'"
        f" text-anchor='middle'>{label}</text>"
        f"<text x='{left_width + right_width / 2}' y='14' fill='#fff' font-family='{font_family}'"
        f" font-size='11' text-anchor='middle'>{value}</text>"
        "</svg>"
    )


def _tier_color(tier: str) -> str:
    palette = {
        "gold": "#f59e0b",
        "silver": "#9ca3af",
        "bronze": "#d97706",
        "platinum": "#e5e7eb",
        "blue": "#3b82f6",
        "green": "#22c55e",
        "gray": "#6b7280",
    }
    return palette.get(tier, "#6b7280")


async def _badge_label(session: AsyncSession, agent_id: str, owner_verified: bool) -> tuple[str, str]:
    cert_result = await session.execute(
        select(Seal)
        .join(AgentSeal, AgentSeal.seal_id == Seal.id)
        .where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
            Seal.category == "certification",
        )
    )
    cert_seals = cert_result.scalars().all()
    if cert_seals:
        tier_priority = {"gold": 3, "silver": 2, "bronze": 1}
        cert_seals.sort(key=lambda seal: tier_priority.get(seal.tier or "", 0), reverse=True)
        top = cert_seals[0]
        stars = {"gold": "★★★", "silver": "★★", "bronze": "★"}.get(top.tier or "", "")
        label = f"{top.name} {stars}".strip()
        return label, _tier_color(top.tier or "gold")

    if owner_verified:
        return "Verified", _tier_color("green")

    seal_count_result = await session.execute(
        select(func.count())
        .select_from(AgentSeal)
        .where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
        )
    )
    seal_count = seal_count_result.scalar_one() or 0
    if seal_count > 0:
        return f"{seal_count} seals", _tier_color("blue")

    return "Unverified", _tier_color("gray")


@router.get("/{agent_id}/trust", response_model=TrustScoreResponse)
async def get_trust_score(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    breakdown = await compute_trust_breakdown(session, agent)
    return TrustScoreResponse(**breakdown)


@router.get("/{agent_id}/badge.svg")
async def agent_badge(agent_id: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    value, color = await _badge_label(session, agent.id, agent.owner_verified)
    svg = _build_badge_svg("AgentSeal", value, color)
    headers = {"Cache-Control": "public, max-age=3600"}
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


@router.get("/by-slug/{slug}/badge.svg")
async def agent_badge_by_slug(slug: str, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_slug(session, slug)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    value, color = await _badge_label(session, agent.id, agent.owner_verified)
    svg = _build_badge_svg("AgentSeal", value, color)
    headers = {"Cache-Control": "public, max-age=3600"}
    return Response(content=svg, media_type="image/svg+xml", headers=headers)
