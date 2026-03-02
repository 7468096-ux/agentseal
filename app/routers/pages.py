from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Agent, AgentSeal, Seal, CertTest, CertAttempt
from app.services.agent_service import get_agent_by_id, get_agent_by_slug, profile_url
from app.services.behaviour_service import get_agent_stats
from app.services.trust_service import compute_trust_breakdown

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, session: AsyncSession = Depends(get_session)):
    cert_tests = (
        await session.execute(select(CertTest).where(CertTest.is_active == True).order_by(CertTest.price_cents))
    ).scalars().all()

    agent_count_result = await session.execute(select(func.count()).select_from(Agent))
    agent_count = agent_count_result.scalar_one() or 0

    seal_count_result = await session.execute(select(func.count()).select_from(AgentSeal))
    seal_count = seal_count_result.scalar_one() or 0

    cert_count_result = await session.execute(
        select(func.count()).select_from(CertAttempt).where(CertAttempt.passed == True)
    )
    cert_count = cert_count_result.scalar_one() or 0

    featured_result = await session.execute(
        select(Agent)
        .where(Agent.is_active == True)
        .order_by(Agent.trust_score.desc().nullslast(), Agent.created_at.desc())
        .limit(4)
    )
    featured_agents = []
    for agent in featured_result.scalars().all():
        trust = await compute_trust_breakdown(session, agent)
        seal_rows = (
            await session.execute(
                select(AgentSeal, Seal)
                .join(Seal, AgentSeal.seal_id == Seal.id)
                .where(
                    AgentSeal.agent_id == agent.id,
                    AgentSeal.revoked == False,
                    or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
                )
                .order_by(AgentSeal.issued_at.desc())
                .limit(3)
            )
        ).all()
        top_seals = [
            {
                "name": seal.name,
                "icon_emoji": seal.icon_emoji,
                "category": seal.category,
            }
            for _, seal in seal_rows
        ]
        featured_agents.append(
            {
                "name": agent.name,
                "slug": agent.slug,
                "platform": agent.platform,
                "avatar_url": agent.avatar_url,
                "trust_score": trust["total_score"],
                "top_seals": top_seals,
                "profile_url": profile_url(agent.slug),
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "featured_agents": featured_agents,
            "cert_tests": cert_tests,
            "stats": {
                "agent_count": agent_count,
                "seal_count": seal_count,
                "cert_count": cert_count,
            },
        },
    )


@router.get("/@{slug}", response_class=HTMLResponse)
async def profile(slug: str, request: Request, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_slug(session, slug)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    agent_seals = (
        await session.execute(
            select(AgentSeal, Seal)
            .join(Seal, AgentSeal.seal_id == Seal.id)
            .where(
                AgentSeal.agent_id == agent.id,
                AgentSeal.revoked == False,
                or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
            )
        )
    ).all()

    seals = [
        {
            "name": seal.name,
            "slug": seal.slug,
            "icon_emoji": seal.icon_emoji,
            "color": seal.color,
            "category": seal.category,
        }
        for _, seal in agent_seals
    ]

    trust = await compute_trust_breakdown(session, agent)
    behaviour_stats = await get_agent_stats(session, str(agent.id))

    badge_url = f"{settings.app_url}/v1/agents/by-slug/{agent.slug}/badge.svg"
    reported = request.query_params.get("reported") == "1"

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "agent": agent,
            "seals": seals,
            "profile_url": profile_url(agent.slug),
            "trust": trust,
            "behaviour": behaviour_stats,
            "badge_url": badge_url,
            "badge_embed": f"<img src=\"{badge_url}\" alt=\"AgentSeal badge\" />",
            "reported": reported,
        },
    )


@router.get("/directory", response_class=HTMLResponse)
async def directory(request: Request, session: AsyncSession = Depends(get_session)):
    q = request.query_params.get("q")
    platform = request.query_params.get("platform")
    tier = request.query_params.get("tier")
    sort = request.query_params.get("sort") or "trust_score"
    try:
        limit = int(request.query_params.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    try:
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    filters = [Agent.is_active == True]
    if q:
        query = f"%{q.strip()}%"
        filters.append(or_(Agent.name.ilike(query), Agent.slug.ilike(query), Agent.description.ilike(query)))
    if platform:
        filters.append(Agent.platform == platform)
    if tier:
        filters.append(Agent.trust_tier == tier)

    total_result = await session.execute(select(func.count()).select_from(Agent).where(*filters))
    total = total_result.scalar_one() or 0

    statement = (
        select(Agent, func.count(AgentSeal.id).label("seal_count"))
        .outerjoin(
            AgentSeal,
            (
                (Agent.id == AgentSeal.agent_id)
                & (AgentSeal.revoked == False)
                & (or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()))
            ),
        )
        .where(*filters)
        .group_by(Agent.id)
    )

    if sort == "name":
        statement = statement.order_by(Agent.name.asc())
    elif sort == "created_at":
        statement = statement.order_by(Agent.created_at.desc())
    else:
        statement = statement.order_by(Agent.trust_score.desc().nullslast(), Agent.created_at.desc())

    counts = (await session.execute(statement.offset(offset).limit(limit))).all()

    agents = [
        {
            "id": str(agent.id),
            "name": agent.name,
            "slug": agent.slug,
            "platform": agent.platform,
            "seal_count": seal_count,
            "profile_url": profile_url(agent.slug),
        }
        for agent, seal_count in counts
    ]

    return templates.TemplateResponse(
        "directory.html",
        {
            "request": request,
            "agents": agents,
            "count": len(agents),
            "total": total,
            "q": q or "",
            "platform": platform or "",
            "tier": tier or "",
            "sort": sort,
        },
    )


@router.get("/seals", response_class=HTMLResponse)
async def seals_page(request: Request, session: AsyncSession = Depends(get_session)):
    seals = (
        await session.execute(select(Seal).where(Seal.is_active == True).order_by(Seal.category, Seal.name))
    ).scalars().all()

    category_map = {
        "certification": "🎓 Certification",
        "milestone": "🏆 Milestone",
        "quality": "⭐ Quality",
        "community": "🤝 Community",
        "vanity": "🎨 Vanity",
        "self-declared": "📋 Self-declared",
    }
    grouped = {key: [] for key in category_map.keys()}
    for seal in seals:
        grouped.setdefault(seal.category, []).append(seal)

    return templates.TemplateResponse(
        "seals.html",
        {
            "request": request,
            "grouped_seals": grouped,
            "category_map": category_map,
        },
    )


@router.get("/getting-started", response_class=HTMLResponse)
async def getting_started(request: Request):
    return templates.TemplateResponse("getting_started.html", {"request": request})


@router.get("/claim/{agent_id}", response_class=HTMLResponse)
async def claim_page(agent_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    agent = await get_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    return templates.TemplateResponse(
        "claim.html",
        {
            "request": request,
            "agent": agent,
            "claim_endpoint": f"/v1/agents/{agent.id}/claim",
        },
    )
