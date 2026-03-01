from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BehaviourReportCreate(BaseModel):
    reporter_type: str = Field(default="agent")
    report_type: str
    outcome: str
    details: Optional[dict[str, Any]] = None
    weight: float = Field(default=1.0, ge=0)


class BehaviourReportResponse(BaseModel):
    id: str
    subject_agent_id: str
    reporter_agent_id: Optional[str]
    reporter_type: str
    report_type: str
    outcome: str
    details: Optional[dict[str, Any]]
    weight: float
    created_at: datetime


class BehaviourReportListResponse(BaseModel):
    reports: list[BehaviourReportResponse]
    total: int
    limit: int
    offset: int


class BehaviourStatsResponse(BaseModel):
    total_reports: int
    success_count: int
    failure_count: int
    success_rate: float
    average_weight: float
    breakdown_by_type: dict[str, int]
