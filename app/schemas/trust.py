from __future__ import annotations

from pydantic import BaseModel


class TrustScoreResponse(BaseModel):
    total_score: float
    tier: str
    certification_score: float
    behaviour_score: float
    tenure_score: float
    activity_score: float
    verification_score: float
    seal_count_score: float
    report_count: int
    success_rate: float
    seal_count: int
