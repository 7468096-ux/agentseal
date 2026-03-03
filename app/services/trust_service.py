from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, AgentSeal, BehaviourReport, Seal

# ---------------------------------------------------------------------------
# Grade thresholds (descending)
# ---------------------------------------------------------------------------
GRADE_THRESHOLDS = [
    (950, "SSS"),
    (850, "SS"),
    (750, "S"),
    (600, "A"),
    (450, "B"),
    (300, "C"),
    (150, "D"),
    (0, "F"),
]

# Certification tier point values
CERT_TIER_POINTS = {"gold": 200, "silver": 100, "bronze": 50}
CERT_EXTRA_BONUS = 10  # per additional cert beyond the first
CERT_MAX = 300

# Behaviour
BEHAVIOUR_BASE_MULTIPLIER = 200  # success_rate * 200
BEHAVIOUR_REPORT_BONUS = 5  # per report
BEHAVIOUR_REPORT_BONUS_CAP = 50
BEHAVIOUR_CONFIDENCE_THRESHOLD = 10  # below this, apply confidence factor
BEHAVIOUR_MAX = 250

# Activity — recency based on latest report (linear decay over 30 days)
ACTIVITY_DECAY_DAYS = 30
ACTIVITY_MAX = 200

# Tenure — linear over 365 days
TENURE_DAYS_FOR_MAX = 365
TENURE_MAX = 150

# Identity — profile completeness
IDENTITY_MAX = 100

# Algorithm version (bump when formula changes)
ALGORITHM_VERSION = "2.0"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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


async def _get_report_stats(session: AsyncSession, agent_id: str) -> tuple[int, int]:
    """Return (total_reports, success_count)."""
    total_result = await session.execute(
        select(func.count())
        .select_from(BehaviourReport)
        .where(BehaviourReport.subject_agent_id == agent_id)
    )
    total_reports = total_result.scalar_one() or 0

    success_result = await session.execute(
        select(func.count())
        .select_from(BehaviourReport)
        .where(
            BehaviourReport.subject_agent_id == agent_id,
            BehaviourReport.outcome == "success",
        )
    )
    success_count = success_result.scalar_one() or 0

    return total_reports, success_count


async def _get_latest_report_date(session: AsyncSession, agent_id: str) -> datetime | None:
    result = await session.execute(
        select(func.max(BehaviourReport.created_at))
        .where(BehaviourReport.subject_agent_id == agent_id)
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Score components
# ---------------------------------------------------------------------------


def _certification_score(tiers: list[str]) -> float:
    """Certification 30 % — max 300.

    Best cert: Gold 200, Silver 100, Bronze 50.
    +10 per additional cert (beyond the first), capped at CERT_MAX.
    """
    if not tiers:
        return 0.0

    # Sort by value desc to pick best first
    sorted_tiers = sorted(tiers, key=lambda t: CERT_TIER_POINTS.get(t, 0), reverse=True)
    best = CERT_TIER_POINTS.get(sorted_tiers[0], 0)
    extras = len(sorted_tiers) - 1
    bonus = min(extras * CERT_EXTRA_BONUS, CERT_MAX - best)
    return min(float(best + bonus), CERT_MAX)


def _behaviour_score(total_reports: int, success_count: int) -> float:
    """Behaviour 25 % — max 250.

    Base: success_rate * 200
    Bonus: +5 per report, capped at +50
    Confidence: if total_reports < 10, multiply by total_reports / 10
    """
    if total_reports == 0:
        return 0.0

    success_rate = success_count / total_reports
    base = success_rate * BEHAVIOUR_BASE_MULTIPLIER
    report_bonus = min(total_reports * BEHAVIOUR_REPORT_BONUS, BEHAVIOUR_REPORT_BONUS_CAP)
    raw = base + report_bonus

    if total_reports < BEHAVIOUR_CONFIDENCE_THRESHOLD:
        raw *= total_reports / BEHAVIOUR_CONFIDENCE_THRESHOLD

    return min(round(raw, 4), BEHAVIOUR_MAX)


def _activity_score(latest_report_at: datetime | None) -> float:
    """Activity 20 % — max 200.

    Linear decay from 200 to 0 over ACTIVITY_DECAY_DAYS since the latest
    report's created_at.  No reports → 0.
    """
    if latest_report_at is None:
        return 0.0

    now = datetime.now(timezone.utc)
    if latest_report_at.tzinfo is None:
        latest_report_at = latest_report_at.replace(tzinfo=timezone.utc)

    days_since = max((now - latest_report_at).total_seconds() / 86400, 0)
    if days_since >= ACTIVITY_DECAY_DAYS:
        return 0.0
    return round(ACTIVITY_MAX * (1 - days_since / ACTIVITY_DECAY_DAYS), 4)


def _tenure_score(created_at: datetime | None) -> float:
    """Tenure 15 % — max 150.  Linear over 365 days."""
    if not created_at:
        return 0.0

    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    days = max((now - created_at).days, 0)
    return min(round(days / TENURE_DAYS_FOR_MAX * TENURE_MAX, 4), TENURE_MAX)


def _identity_score(agent: Agent) -> float:
    """Identity 10 % — max 100.

    avatar_url present  → +20
    owner_verified      → +30
    website_url present → +20
    description present → +30
    """
    score = 0.0
    if agent.avatar_url:
        score += 20.0
    if agent.owner_verified:
        score += 30.0
    if agent.website_url:
        score += 20.0
    if agent.description:
        score += 30.0
    return min(score, IDENTITY_MAX)


def _grade_for_score(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def compute_trust_breakdown(session: AsyncSession, agent: Agent) -> dict:
    """Compute the full trust-score breakdown for an agent."""
    certification_tiers = await _get_certification_tiers(session, agent.id)
    cert = _certification_score(certification_tiers)

    total_reports, success_count = await _get_report_stats(session, agent.id)
    success_rate = success_count / total_reports if total_reports else 0.0
    behav = _behaviour_score(total_reports, success_count)

    latest_report_at = await _get_latest_report_date(session, agent.id)
    activity = _activity_score(latest_report_at)

    tenure = _tenure_score(agent.created_at)
    identity = _identity_score(agent)

    total_score = round(cert + behav + activity + tenure + identity, 2)
    grade = _grade_for_score(total_score)

    return {
        "total_score": total_score,
        "grade": grade,
        "certification_score": round(cert, 2),
        "behaviour_score": round(behav, 2),
        "activity_score": round(activity, 2),
        "tenure_score": round(tenure, 2),
        "identity_score": round(identity, 2),
        "report_count": total_reports,
        "success_rate": round(success_rate, 4),
        "certification_count": len(certification_tiers),
    }


async def recalculate_trust_score(session: AsyncSession, agent: Agent) -> dict:
    """Recompute and persist trust_score + trust_tier on the Agent row."""
    breakdown = await compute_trust_breakdown(session, agent)
    agent.trust_score = breakdown["total_score"]
    agent.trust_tier = breakdown["grade"]
    session.add(agent)
    await session.flush()
    return breakdown


def get_algorithm_spec() -> dict:
    """Return a machine-readable description of the scoring algorithm."""
    return {
        "version": ALGORITHM_VERSION,
        "max_score": 1000,
        "components": {
            "certification": {
                "weight": "30%",
                "max": CERT_MAX,
                "tiers": CERT_TIER_POINTS,
                "extra_cert_bonus": CERT_EXTRA_BONUS,
            },
            "behaviour": {
                "weight": "25%",
                "max": BEHAVIOUR_MAX,
                "base": f"success_rate * {BEHAVIOUR_BASE_MULTIPLIER}",
                "report_bonus": f"+{BEHAVIOUR_REPORT_BONUS}/report, cap {BEHAVIOUR_REPORT_BONUS_CAP}",
                "confidence_threshold": BEHAVIOUR_CONFIDENCE_THRESHOLD,
            },
            "activity": {
                "weight": "20%",
                "max": ACTIVITY_MAX,
                "method": f"linear decay over {ACTIVITY_DECAY_DAYS} days from latest report",
            },
            "tenure": {
                "weight": "15%",
                "max": TENURE_MAX,
                "method": f"linear over {TENURE_DAYS_FOR_MAX} days",
            },
            "identity": {
                "weight": "10%",
                "max": IDENTITY_MAX,
                "fields": {
                    "avatar_url": 20,
                    "owner_verified": 30,
                    "website_url": 20,
                    "description": 30,
                },
            },
        },
        "grades": {g: t for t, g in GRADE_THRESHOLDS},
    }
