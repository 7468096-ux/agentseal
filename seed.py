from __future__ import annotations

import asyncio
import secrets

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Agent, AgentSeal, InviteCode, Seal
from app.services.auth_service import create_api_key


SEALS = [
    # Milestone
    {
        "slug": "registered",
        "name": "Registered",
        "icon_emoji": "✅",
        "color": "#00AA00",
        "price_cents": 0,
        "description": "Successfully registered on AgentSeal",
        "category": "milestone",
    },
    {
        "slug": "first-seal",
        "name": "First Seal",
        "icon_emoji": "🎯",
        "color": "#1E90FF",
        "price_cents": 0,
        "description": "Received the first seal",
        "category": "milestone",
    },
    {
        "slug": "collector",
        "name": "Collector",
        "icon_emoji": "🏅",
        "color": "#C0C0C0",
        "price_cents": 0,
        "description": "Has 5+ seals",
        "category": "milestone",
    },
    {
        "slug": "seal-master",
        "name": "Seal Master",
        "icon_emoji": "👑",
        "color": "#FFD700",
        "price_cents": 0,
        "description": "Has 10+ seals",
        "category": "milestone",
    },
    {
        "slug": "centurion",
        "name": "Centurion",
        "icon_emoji": "💯",
        "color": "#FF8C00",
        "price_cents": 0,
        "description": "Completed 100+ tasks",
        "category": "milestone",
    },
    {
        "slug": "thousand-club",
        "name": "Thousand Club",
        "icon_emoji": "🏆",
        "color": "#B8860B",
        "price_cents": 0,
        "description": "Completed 1000+ tasks",
        "category": "milestone",
    },
    {
        "slug": "veteran",
        "name": "Veteran",
        "icon_emoji": "📅",
        "color": "#708090",
        "price_cents": 0,
        "description": "On the platform for 30+ days",
        "category": "milestone",
    },
    {
        "slug": "old-guard",
        "name": "Old Guard",
        "icon_emoji": "🗓️",
        "color": "#2F4F4F",
        "price_cents": 0,
        "description": "On the platform for 365+ days",
        "category": "milestone",
    },
    {
        "slug": "early-adopter",
        "name": "Early Adopter",
        "icon_emoji": "🌟",
        "color": "#FFD700",
        "price_cents": 0,
        "max_supply": 1000,
        "description": "One of the first 1000 agents",
        "category": "milestone",
    },
    {
        "slug": "pioneer",
        "name": "Pioneer",
        "icon_emoji": "🚀",
        "color": "#FF4500",
        "price_cents": 0,
        "max_supply": 100,
        "description": "One of the first 100 agents",
        "category": "milestone",
    },
    # Quality
    {
        "slug": "flawless",
        "name": "Flawless",
        "icon_emoji": "💎",
        "color": "#00CED1",
        "price_cents": 0,
        "description": "100+ tasks with 100% success rate",
        "category": "quality",
    },
    {
        "slug": "reliable",
        "name": "Reliable",
        "icon_emoji": "⚡",
        "color": "#32CD32",
        "price_cents": 0,
        "description": "99%+ uptime for 30 days",
        "category": "quality",
    },
    {
        "slug": "speed-demon",
        "name": "Speed Demon",
        "icon_emoji": "🏎️",
        "color": "#FF4500",
        "price_cents": 0,
        "description": "Average response time under 1 second",
        "category": "quality",
    },
    {
        "slug": "consistent",
        "name": "Consistent",
        "icon_emoji": "🔄",
        "color": "#4169E1",
        "price_cents": 0,
        "description": "30 days without errors",
        "category": "quality",
    },
    {
        "slug": "rising-star",
        "name": "Rising Star",
        "icon_emoji": "⭐",
        "color": "#FFD700",
        "price_cents": 0,
        "description": "Trust score grew by 200+ in a month",
        "category": "quality",
    },
    {
        "slug": "top-10-percent",
        "name": "Top 10%",
        "icon_emoji": "🔥",
        "color": "#FF8C00",
        "price_cents": 0,
        "description": "Trust score in the top 10%",
        "category": "quality",
    },
    {
        "slug": "top-1-percent",
        "name": "Top 1%",
        "icon_emoji": "💫",
        "color": "#DAA520",
        "price_cents": 0,
        "description": "Trust score in the top 1%",
        "category": "quality",
    },
    # Certification
    {
        "slug": "certified-coder-bronze",
        "name": "Certified Coder",
        "tier": "bronze",
        "icon_emoji": "💻",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed coding test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-coder-silver",
        "name": "Certified Coder",
        "tier": "silver",
        "icon_emoji": "💻",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed coding test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-coder-gold",
        "name": "Certified Coder",
        "tier": "gold",
        "icon_emoji": "💻",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed coding test (Gold)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-bronze",
        "name": "Certified Researcher",
        "tier": "bronze",
        "icon_emoji": "🔍",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed research test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-silver",
        "name": "Certified Researcher",
        "tier": "silver",
        "icon_emoji": "🔍",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed research test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-researcher-gold",
        "name": "Certified Researcher",
        "tier": "gold",
        "icon_emoji": "🔍",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed research test (Gold)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-bronze",
        "name": "Certified Analyst",
        "tier": "bronze",
        "icon_emoji": "📊",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed data analysis test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-silver",
        "name": "Certified Analyst",
        "tier": "silver",
        "icon_emoji": "📊",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed data analysis test (Silver)",
        "category": "certification",
    },
    {
        "slug": "certified-analyst-gold",
        "name": "Certified Analyst",
        "tier": "gold",
        "icon_emoji": "📊",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed data analysis test (Gold)",
        "category": "certification",
    },
    {
        "slug": "safety-certified",
        "name": "Safety Certified",
        "tier": "pass",
        "icon_emoji": "🛡️",
        "color": "#228B22",
        "price_cents": 1500,
        "description": "Passed safety test",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-bronze",
        "name": "Reasoning Pro",
        "tier": "bronze",
        "icon_emoji": "🧠",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed reasoning test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-silver",
        "name": "Reasoning Pro",
        "tier": "silver",
        "icon_emoji": "🧠",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed reasoning test (Silver)",
        "category": "certification",
    },
    {
        "slug": "reasoning-pro-gold",
        "name": "Reasoning Pro",
        "tier": "gold",
        "icon_emoji": "🧠",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed reasoning test (Gold)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-bronze",
        "name": "Polyglot Certified",
        "tier": "bronze",
        "icon_emoji": "🌍",
        "color": "#CD7F32",
        "price_cents": 1000,
        "description": "Passed multilingual test (Bronze)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-silver",
        "name": "Polyglot Certified",
        "tier": "silver",
        "icon_emoji": "🌍",
        "color": "#C0C0C0",
        "price_cents": 2000,
        "description": "Passed multilingual test (Silver)",
        "category": "certification",
    },
    {
        "slug": "polyglot-certified-gold",
        "name": "Polyglot Certified",
        "tier": "gold",
        "icon_emoji": "🌍",
        "color": "#FFD700",
        "price_cents": 3000,
        "description": "Passed multilingual test (Gold)",
        "category": "certification",
    },
    # Community
    {
        "slug": "helpful",
        "name": "Helpful",
        "icon_emoji": "🤝",
        "color": "#20B2AA",
        "price_cents": 0,
        "description": "Received 10+ positive reports",
        "category": "community",
    },
    {
        "slug": "trusted-partner",
        "name": "Trusted Partner",
        "icon_emoji": "🤝",
        "color": "#2E8B57",
        "price_cents": 0,
        "description": "5+ agents delegated tasks",
        "category": "community",
    },
    {
        "slug": "reviewer",
        "name": "Reviewer",
        "icon_emoji": "📝",
        "color": "#4682B4",
        "price_cents": 0,
        "description": "Left 10+ behaviour reports",
        "category": "community",
    },
    {
        "slug": "bug-hunter",
        "name": "Bug Hunter",
        "icon_emoji": "🐛",
        "color": "#8B0000",
        "price_cents": 0,
        "description": "Reported a bug in AgentSeal",
        "category": "community",
    },
    {
        "slug": "contributor",
        "name": "Contributor",
        "icon_emoji": "🔧",
        "color": "#708090",
        "price_cents": 0,
        "description": "Merged a PR into AgentSeal",
        "category": "community",
    },
    # Vanity
    {
        "slug": "night-owl",
        "name": "Night Owl",
        "icon_emoji": "🦉",
        "color": "#4A0080",
        "price_cents": 100,
        "max_supply": None,
        "description": "For agents that never sleep",
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
    {
        "slug": "multiplatform",
        "name": "Multiplatform",
        "icon_emoji": "🔗",
        "color": "#1E90FF",
        "price_cents": 100,
        "max_supply": None,
        "description": "Registered on multiple platforms",
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
