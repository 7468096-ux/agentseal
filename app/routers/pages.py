from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Agent, AgentSeal, Seal, CertTest
from app.services.agent_service import get_agent_by_slug, profile_url

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, session: AsyncSession = Depends(get_session)):
    seals = (await session.execute(select(Seal).where(Seal.is_active == True))).scalars().all()
    cert_tests = (
        await session.execute(select(CertTest).where(CertTest.is_active == True).order_by(CertTest.price_cents))
    ).scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "seals": seals, "cert_tests": cert_tests},
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

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "agent": agent,
            "seals": seals,
            "profile_url": profile_url(agent.slug),
        },
    )


@router.get("/directory", response_class=HTMLResponse)
async def directory(request: Request, session: AsyncSession = Depends(get_session)):
    counts = (
        await session.execute(
            select(Agent, func.count(AgentSeal.id).label("seal_count"))
            .outerjoin(
                AgentSeal,
                (
                    (Agent.id == AgentSeal.agent_id)
                    & (AgentSeal.revoked == False)
                    & (or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()))
                ),
            )
            .group_by(Agent.id)
            .order_by(func.count(AgentSeal.id).desc())
        )
    ).all()

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
        {"request": request, "agents": agents},
    )
