from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Agent, CertAttempt, CertTest
from app.schemas.certification import (
    AttemptResultsResponse,
    CertAttemptResponse,
    CertAttemptTask,
    CertTestListResponse,
    CertTestResponse,
    StartAttemptResponse,
    SubmitAttemptRequest,
    SubmitAttemptResponse,
)
from app.services.certification_service import grade_attempt, issue_certification, start_attempt, submit_answers

router = APIRouter(prefix="/v1", tags=["certification"])


def build_test_response(test: CertTest) -> CertTestResponse:
    return CertTestResponse(
        id=str(test.id),
        category=test.category,
        tier=test.tier,
        name=test.name,
        description=test.description,
        passing_score=test.passing_score,
        task_count=test.task_count,
        time_limit_seconds=test.time_limit_seconds,
        price_cents=test.price_cents,
        cooldown_hours=test.cooldown_hours,
        max_attempts_per_month=test.max_attempts_per_month,
        is_active=test.is_active,
        created_at=test.created_at,
    )


def build_attempt_response(attempt: CertAttempt) -> CertAttemptResponse:
    tasks = [
        CertAttemptTask(
            id=task.get("id"),
            prompt=task.get("prompt"),
            task_type=task.get("task_type"),
            difficulty=task.get("difficulty"),
        )
        for task in (attempt.tasks or [])
    ]
    return CertAttemptResponse(
        id=str(attempt.id),
        test_id=str(attempt.test_id),
        status=attempt.status,
        tasks=tasks,
        score=attempt.score,
        passed=attempt.passed,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        created_at=attempt.created_at,
    )


@router.get("/certifications", response_model=CertTestListResponse)
async def list_certifications(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CertTest).where(CertTest.is_active == True))
    tests = result.scalars().all()
    return CertTestListResponse(tests=[build_test_response(test) for test in tests], total=len(tests))


@router.get("/certifications/{test_id}", response_model=CertTestResponse)
async def get_certification(test_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CertTest).where(CertTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="certification not found")
    return build_test_response(test)


@router.post("/certifications/{test_id}/attempt", response_model=StartAttemptResponse)
async def start_cert_attempt(test_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(CertTest).where(CertTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="certification not found")

    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(status_code=401, detail="missing api key")

    agent = (await session.execute(select(Agent).where(Agent.id == agent_id))).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    result = await start_attempt(session, agent, test)
    await session.commit()

    if result["type"] == "payment_required":
        payment = result["payment"]
        return StartAttemptResponse(
            payment_required=True,
            checkout_url=result.get("checkout_url"),
            payment_id=str(payment.id),
            expires_in_seconds=result.get("expires_in_seconds"),
        )

    attempt = result["attempt"]
    return StartAttemptResponse(payment_required=False, attempt=build_attempt_response(attempt))


@router.get("/attempts/{attempt_id}", response_model=CertAttemptResponse)
async def get_attempt(attempt_id: str, session: AsyncSession = Depends(get_session)):
    attempt = (await session.execute(select(CertAttempt).where(CertAttempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="attempt not found")
    return build_attempt_response(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=SubmitAttemptResponse)
async def submit_attempt(
    attempt_id: str,
    payload: SubmitAttemptRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    attempt = (await session.execute(select(CertAttempt).where(CertAttempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="attempt not found")

    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id or str(attempt.agent_id) != agent_id:
        raise HTTPException(status_code=403, detail="forbidden")

    test = (await session.execute(select(CertTest).where(CertTest.id == attempt.test_id))).scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="certification not found")

    await submit_answers(session, attempt, payload.answers)
    await grade_attempt(session, attempt, test)
    await issue_certification(session, attempt, test)
    await session.commit()

    return SubmitAttemptResponse(
        attempt_id=str(attempt.id),
        status=attempt.status,
        score=attempt.score,
        passed=attempt.passed,
    )


@router.get("/attempts/{attempt_id}/results", response_model=AttemptResultsResponse)
async def get_attempt_results(attempt_id: str, session: AsyncSession = Depends(get_session)):
    attempt = (await session.execute(select(CertAttempt).where(CertAttempt.id == attempt_id))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="attempt not found")

    return AttemptResultsResponse(
        id=str(attempt.id),
        score=attempt.score,
        passed=attempt.passed,
        results=attempt.results,
        completed_at=attempt.completed_at,
    )
