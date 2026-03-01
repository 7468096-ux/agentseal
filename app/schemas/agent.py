from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class AgentBase(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=64)
    description: Optional[str] = None
    platform: Optional[str] = "custom"
    owner_email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    website_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AgentCreate(AgentBase):
    invite_code: str = Field(min_length=4, max_length=64)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=64)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=64)
    description: Optional[str] = None
    platform: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    website_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AgentSealSummary(BaseModel):
    id: str
    seal_name: str
    seal_slug: str
    category: str
    tier: Optional[str]
    icon_emoji: Optional[str]
    color: Optional[str]
    issued_at: datetime
    expires_at: Optional[datetime]


class AgentResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    platform: str
    owner_verified: bool
    avatar_url: Optional[str]
    website_url: Optional[str]
    metadata: dict[str, Any]
    seals: list[AgentSealSummary]
    created_at: datetime
    profile_url: str


class AgentProfileResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    platform: str
    owner_verified: bool
    avatar_url: Optional[str]
    website_url: Optional[str]
    metadata: dict[str, Any]
    seals: list[AgentSealSummary]
    seal_count: int
    created_at: datetime
    profile_url: str


class AgentCreateResponse(BaseModel):
    agent: AgentResponse
    api_key: str
    warning: str


class AgentCardResponse(BaseModel):
    name: str
    description: Optional[str]
    url: str
    provider: dict[str, str]
    version: str
    capabilities: dict[str, Any]
    authentication: dict[str, list[str]]
