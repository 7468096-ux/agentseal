from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr


class ClaimCreate(BaseModel):
    email: EmailStr
    verification_method: Literal["email", "github"]


class ClaimResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    verification_method: str
    message: str


class ClaimApproveResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    api_key: str
    message: str
