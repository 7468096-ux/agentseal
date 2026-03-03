from __future__ import annotations

from pydantic import BaseModel


class TrustScoreResponse(BaseModel):
    total_score: float
    grade: str
    certification_score: float
    behaviour_score: float
    activity_score: float
    tenure_score: float
    identity_score: float
    report_count: int
    success_rate: float
    certification_count: int


class TrustAlgorithmResponse(BaseModel):
    version: str
    max_score: int
    components: dict
    grades: dict
