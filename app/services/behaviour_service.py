from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, BehaviourReport
from app.services.trust_service import recalculate_trust_score

REPORT_TYPES = {"task_completion", "error", "uptime", "feedback", "hallucination"}
OUTCOMES = {"success", "failure", "partial"}
REPORTER_TYPES = {"agent", "user", "platform"}


async def submit_report(
    session: AsyncSession,
    subject_agent: Agent,
    reporter_agent: Agent | None,
    data: dict,
) -> BehaviourReport:
    reporter_type = data.get("reporter_type") or "agent"
    report_type = data.get("report_type")
    outcome = data.get("outcome")

    if reporter_type not in REPORTER_TYPES:
        raise HTTPException(status_code=400, detail="invalid reporter_type")
    if report_type not in REPORT_TYPES:
        raise HTTPException(status_code=400, detail="invalid report_type")
    if outcome not in OUTCOMES:
        raise HTTPException(status_code=400, detail="invalid outcome")

    if reporter_type == "agent" and not reporter_agent:
        raise HTTPException(status_code=400, detail="reporter_agent required")

    weight = data.get("weight", 1.0)
    if weight < 0:
        raise HTTPException(status_code=400, detail="invalid weight")

    report = BehaviourReport(
        subject_agent_id=subject_agent.id,
        reporter_agent_id=reporter_agent.id if reporter_agent and reporter_type == "agent" else None,
        reporter_type=reporter_type,
        report_type=report_type,
        outcome=outcome,
        details=data.get("details") or {},
        weight=weight,
    )
    session.add(report)
    await session.flush()

    await recalculate_trust_score(session, subject_agent)

    return report


async def get_agent_stats(session: AsyncSession, agent_id: str) -> dict:
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

    failure_result = await session.execute(
        select(func.count())
        .select_from(BehaviourReport)
        .where(BehaviourReport.subject_agent_id == agent_id, BehaviourReport.outcome == "failure")
    )
    failure_count = failure_result.scalar_one() or 0

    avg_weight_result = await session.execute(
        select(func.avg(BehaviourReport.weight)).where(BehaviourReport.subject_agent_id == agent_id)
    )
    average_weight = avg_weight_result.scalar_one() or 0.0

    breakdown_result = await session.execute(
        select(BehaviourReport.report_type, func.count())
        .where(BehaviourReport.subject_agent_id == agent_id)
        .group_by(BehaviourReport.report_type)
    )
    breakdown = {row[0]: row[1] for row in breakdown_result.all()}

    success_rate = round(success_count / total_reports, 4) if total_reports else 0.0

    return {
        "total_reports": total_reports,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": success_rate,
        "average_weight": float(round(average_weight, 4)) if average_weight is not None else 0.0,
        "breakdown_by_type": breakdown,
    }
