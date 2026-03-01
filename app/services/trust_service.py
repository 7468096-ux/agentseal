from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, AgentSeal, BehaviourReport, Seal

TIER_THRESHOLDS = [
    (800, "platinum"),
    (600, "gold"),
    (400, "silver"),
    (200, "bronze"),
    (0, "unverified"),
]


async def _get_active_seal_count(session: AsyncSession, agent_id: str) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(AgentSeal)
        .where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
        )
    )
    return result.scalar_one() or 0


async def _get_certification_tiers(session: AsyncSession, agent_id: str) -> list[str]:
    result = await session.execute(
        select(Seal.tier)
        .join(AgentSeal, AgentSeal.seal_id == Seal.id)
        .where(
            AgentSeal.agent_id == agent_id,
            AgentSeal.revoked == False,
            or_(AgentSeal.expires_at.is_(None), AgentSeal.expires_at > func.now()),
            Seal.category == "certification",
        )
    )
    return [row[0] for row in result.all() if row[0]]


async def _get_report_stats(session: AsyncSession, agent_id: str) -> tuple[int, float]:
    total_result = await session.execute(
        select(func.count()).select_from(BehaviourReport).where(BehaviourReport.subject_agent_id == agent_id)
    )
    total_reports = total_result.scalar_one() or 0

    success_result = await session.execute(
        select(func.count())
        .select_from(BehaviourReport)
        .where(BehaviourReport.subject_agent_id == agent_id, BehaviourReport.outcome == "success")
    )
    success_count = success_result.scalar_one() or 0

    success_rate = success_count / total_reports if total_reports else 0.0
    return total_reports, success_rate


def _certification_score_from_tiers(tiers: list[str]) -> float:
    if not tiers:
        return 0.0
    if "gold" in tiers:
        return 300.0
    if "silver" in tiers:
        return 200.0
    if "bronze" in tiers:
        return 100.0
    return 0.0


def _tier_for_score(score: float) -> str:
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "unverified"


async def compute_trust_breakdown(session: AsyncSession, agent: Agent) -> dict:
    certification_tiers = await _get_certification_tiers(session, agent.id)
    certification_score = _certification_score_from_tiers(certification_tiers)

    report_count, success_rate = await _get_report_stats(session, agent.id)
    behaviour_score = (success_rate * 300.0) if report_count >= 10 else 0.0

    created_at = agent.created_at
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if created_at:
        now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.utcnow()
        days_on_platform = (now - created_at).days
    else:
        days_on_platform = 0
    tenure_score = min((days_on_platform / 365.0) * 100.0, 100.0)

    activity_score = min(report_count / 100.0, 1.0) * 100.0
    verification_score = 100.0 if agent.owner_verified else 0.0

    seal_count = await _get_active_seal_count(session, agent.id)
    seal_count_score = min(seal_count / 10.0, 1.0) * 100.0

    total_score = round(
        certification_score + behaviour_score + tenure_score + activity_score + verification_score + seal_count_score,
        4,
    )
    tier = _tier_for_score(total_score)

    return {
        "total_score": total_score,
        "tier": tier,
        "certification_score": round(certification_score, 4),
        "behaviour_score": round(behaviour_score, 4),
        "tenure_score": round(tenure_score, 4),
        "activity_score": round(activity_score, 4),
        "verification_score": round(verification_score, 4),
        "seal_count_score": round(seal_count_score, 4),
        "report_count": report_count,
        "success_rate": round(success_rate, 4),
        "seal_count": seal_count,
    }


async def recalculate_trust_score(session: AsyncSession, agent: Agent) -> dict:
    breakdown = await compute_trust_breakdown(session, agent)
    agent.trust_score = breakdown["total_score"]
    agent.trust_tier = breakdown["tier"]
    session.add(agent)
    await session.flush()
    return breakdown
