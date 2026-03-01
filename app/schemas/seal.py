from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class SealResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    tier: Optional[str]
    price_cents: int
    price_display: str
    icon_emoji: Optional[str]
    color: Optional[str]
    max_supply: Optional[int]
    issued_count: int
    available: bool


class SealListResponse(BaseModel):
    seals: list[SealResponse]
    total: int
    limit: int
    offset: int


class SealDetailAgent(BaseModel):
    id: str
    name: str
    slug: str
    profile_url: str


class SealDetailResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    tier: Optional[str]
    price_cents: int
    price_display: str
    icon_emoji: Optional[str]
    color: Optional[str]
    max_supply: Optional[int]
    issued_count: int
    is_active: bool
    requirements: Optional[dict[str, Any]]
    created_at: datetime
    recent_agents: list[SealDetailAgent]


class AgentSealResponse(BaseModel):
    seal_name: str
    seal_slug: str
    category: str
    icon_emoji: Optional[str]
    issued_at: datetime
    expires_at: Optional[datetime]
    revoked: bool


class AgentSealsResponse(BaseModel):
    seals: list[AgentSealResponse]
    count: int


class IssueSealRequest(BaseModel):
    seal_slug: str


class IssueSealFreeResponse(BaseModel):
    agent_seal: dict[str, Any]


class IssueSealPaidResponse(BaseModel):
    payment_required: bool
    checkout_url: str
    payment_id: str
    expires_in_seconds: int
