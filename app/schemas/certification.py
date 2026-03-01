from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CertTestResponse(BaseModel):
    id: str
    category: str
    tier: str
    name: str
    description: str
    passing_score: float
    task_count: int
    time_limit_seconds: int
    price_cents: int
    cooldown_hours: int
    max_attempts_per_month: int
    is_active: bool
    created_at: datetime


class CertTestListResponse(BaseModel):
    tests: list[CertTestResponse]
    total: int


class CertAttemptTask(BaseModel):
    id: str
    prompt: str
    task_type: str
    difficulty: str


class CertAttemptResponse(BaseModel):
    id: str
    test_id: str
    status: str
    tasks: list[CertAttemptTask]
    score: Optional[float]
    passed: Optional[bool]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime


class StartAttemptResponse(BaseModel):
    payment_required: bool = False
    checkout_url: Optional[str] = None
    payment_id: Optional[str] = None
    expires_in_seconds: Optional[int] = None
    attempt: Optional[CertAttemptResponse] = None


class SubmitAttemptRequest(BaseModel):
    answers: dict[str, Any]


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: str
    score: Optional[float]
    passed: Optional[bool]


class AttemptResultsResponse(BaseModel):
    id: str
    score: Optional[float]
    passed: Optional[bool]
    results: Optional[list[dict[str, Any]]]
    completed_at: Optional[datetime]
