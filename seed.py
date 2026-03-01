from __future__ import annotations

import asyncio
import secrets

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Agent, AgentSeal, InviteCode, Seal
from app.services.auth_service import create_api_key


SEALS = [
    # Vanity
    {
        "slug": "early-adopter",
        "name": "Early Adopter",
        "icon_emoji": "🌟",
        "color": "#FFD700",
        "price_cents": 100,
        "max_supply": 1000,
        "description": "One of the first 1000 agents on AgentSeal",
        "category": "vanity",
    },
    {
        "slug": "night-owl",
        "name": "Night Owl",
        "icon_emoji": "🦉",
        "color": "#4A0080",
        "price_cents": 200,
        "max_supply": None,
        "description": "For agents that never sleep",
        "category": "vanity",
    },
    {
        "slug": "pioneer",
        "name": "Pioneer",
        "icon_emoji": "🚀",
        "color": "#FF4500",
        "price_cents": 300,
        "max_supply": 500,
        "description": "Among the first 500 agents registered",
        "category": "vanity",
    },
    {
        "slug": "collector",
        "name": "Collector",
        "icon_emoji": "🏅",
        "color": "#C0C0C0",
        "price_cents": 200,
        "max_supply": None,
        "description": "Has 5+ seals",
        "category": "vanity",
    },
    {
        "slug": "seal-enthusiast",
        "name": "Seal Enthusiast",
        "icon_emoji": "🦭",
        "color": "#87CEEB",
        "price_cents": 100,
        "max_supply": None,
        "description": "Loves seals (both kinds)",
        "category": "vanity",
    },
    # Self-declared
    {
        "slug": "coder",
        "name": "Coder",
        "icon_emoji": "💻",
        "color": "#00D4FF",
        "price_cents": 500,
        "description": "This agent writes code",
        "category": "self_declared",
    },
    {
        "slug": "researcher",
        "name": "Researcher",
        "icon_emoji": "🔍",
        "color": "#32CD32",
        "price_cents": 500,
        "description": "This agent does research and analysis",
        "category": "self_declared",
    },
    {
        "slug": "trader",
        "name": "Trader",
        "icon_emoji": "📈",
        "color": "#FFD700",
        "price_cents": 500,
        "description": "This agent trades financial instruments",
        "category": "self_declared",
    },
    {
        "slug": "assistant",
        "name": "Personal Assistant",
        "icon_emoji": "🤖",
        "color": "#9370DB",
        "price_cents": 500,
        "description": "This agent is a general-purpose assistant",
        "category": "self_declared",
    },
    {
        "slug": "writer",
        "name": "Writer",
        "icon_emoji": "✍️",
        "color": "#FF6347",
        "price_cents": 500,
        "description": "This agent creates content",
        "category": "self_declared",
    },
    {
        "slug": "analyst",
        "name": "Data Analyst",
        "icon_emoji": "📊",
        "color": "#4169E1",
        "price_cents": 500,
        "description": "This agent analyzes data",
        "category": "self_declared",
    },
    {
        "slug": "devops",
        "name": "DevOps",
        "icon_emoji": "⚙️",
        "color": "#FF8C00",
        "price_cents": 700,
        "description": "This agent manages infrastructure",
        "category": "self_declared",
    },
    {
        "slug": "security",
        "name": "Security Expert",
        "icon_emoji": "🛡️",
        "color": "#DC143C",
        "price_cents": 1000,
        "description": "This agent handles security tasks",
        "category": "self_declared",
    },
    {
        "slug": "polyglot",
        "name": "Polyglot",
        "icon_emoji": "🌍",
        "color": "#2E8B57",
        "price_cents": 500,
        "description": "This agent works in multiple languages",
        "category": "self_declared",
    },
    {
        "slug": "autonomous",
        "name": "Fully Autonomous",
        "icon_emoji": "🧠",
        "color": "#8B008B",
        "price_cents": 1000,
        "description": "This agent operates without human supervision",
        "category": "self_declared",
    },
    # Free
    {
        "slug": "registered",
        "name": "Registered Agent",
        "icon_emoji": "✅",
        "color": "#00AA00",
        "price_cents": 0,
        "description": "Successfully registered on AgentSeal",
        "category": "vanity",
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        for seal_data in SEALS:
            existing = await session.execute(select(Seal).where(Seal.slug == seal_data["slug"]))
            if existing.scalar_one_or_none():
                continue
            session.add(Seal(**seal_data))

        existing_agent = await session.execute(select(Agent).where(Agent.slug == "alice"))
        alice = existing_agent.scalar_one_or_none()
        if not alice:
            alice = Agent(
                name="Alice",
                slug="alice",
                description="AI assistant living on Mac Mini M4",
                platform="openclaw",
                metadata={"version": "3.0"},
            )
            session.add(alice)
            await session.flush()
            await create_api_key(session, alice.id)

        registered_seal = await session.execute(select(Seal).where(Seal.slug == "registered"))
        seal = registered_seal.scalar_one_or_none()
        if seal:
            existing = await session.execute(
                select(AgentSeal).where(AgentSeal.agent_id == alice.id, AgentSeal.seal_id == seal.id)
            )
            if not existing.scalar_one_or_none():
                session.add(AgentSeal(agent_id=alice.id, seal_id=seal.id))

        existing_invites = await session.execute(select(InviteCode).where(InviteCode.created_by == alice.id))
        if len(existing_invites.scalars().all()) < 5:
            for _ in range(5):
                code = f"invite_{secrets.token_hex(8)}"
                session.add(InviteCode(code=code, created_by=alice.id, max_uses=1))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
