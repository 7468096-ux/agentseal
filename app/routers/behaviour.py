from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import BehaviourReport
from app.schemas.behaviour import (
    BehaviourReportCreate,
    BehaviourReportListResponse,
    BehaviourReportResponse,
    BehaviourStatsResponse,
)
from app.services.agent_service import get_agent_by_id
from app.services.behaviour_service import get_agent_stats, submit_report

router = APIRouter(prefix="/v1/agents", tags=["behaviour"])


@router.post("/{agent_id}/reports", response_model=BehaviourReportResponse, status_code=201)
async def submit_report_endpoint(
    agent_id: str,
    payload: BehaviourReportCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    subject_agent = await get_agent_by_id(session, agent_id)
    if not subject_agent:
        raise HTTPException(status_code=404, detail="agent not found")

    reporter_agent = None
    reporter_agent_id = getattr(request.state, "agent_id", None)
    if reporter_agent_id:
        reporter_agent = await get_agent_by_id(session, reporter_agent_id)

    report = await submit_report(session, subject_agent, reporter_agent, payload.model_dump(exclude_none=True))
    await session.commit()

    return BehaviourReportResponse(
        id=str(report.id),
        subject_agent_id=str(report.subject_agent_id),
        reporter_agent_id=str(report.reporter_agent_id) if report.reporter_agent_id else None,
        reporter_type=report.reporter_type,
        report_type=report.report_type,
        outcome=report.outcome,
        details=report.details,
        weight=report.weight,
        created_at=report.created_at,
    )


@router.get("/{agent_id}/reports", response_model=BehaviourReportListResponse)
async def list_reports_endpoint(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    subject_agent = await get_agent_by_id(session, agent_id)
    if not subject_agent:
        raise HTTPException(status_code=404, detail="agent not found")

    limit = min(limit, 100)
    total_result = await session.execute(
        select(func.count()).select_from(BehaviourReport).where(BehaviourReport.subject_agent_id == agent_id)
    )
    total = total_result.scalar_one() or 0

    result = await session.execute(
        select(BehaviourReport)
        .where(BehaviourReport.subject_agent_id == agent_id)
        .order_by(BehaviourReport.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reports = result.scalars().all()

    response_reports = [
        BehaviourReportResponse(
            id=str(report.id),
            subject_agent_id=str(report.subject_agent_id),
            reporter_agent_id=str(report.reporter_agent_id) if report.reporter_agent_id else None,
            reporter_type=report.reporter_type,
            report_type=report.report_type,
            outcome=report.outcome,
            details=report.details,
            weight=report.weight,
            created_at=report.created_at,
        )
        for report in reports
    ]

    return BehaviourReportListResponse(reports=response_reports, total=total, limit=limit, offset=offset)


@router.get("/{agent_id}/stats", response_model=BehaviourStatsResponse)
async def agent_stats_endpoint(agent_id: str, session: AsyncSession = Depends(get_session)):
    subject_agent = await get_agent_by_id(session, agent_id)
    if not subject_agent:
        raise HTTPException(status_code=404, detail="agent not found")

    stats = await get_agent_stats(session, agent_id)
    return BehaviourStatsResponse(**stats)
