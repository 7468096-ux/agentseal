from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import ClaimRequest
from app.schemas.claim import ClaimApproveResponse
from app.services.agent_service import get_agent_by_id
from app.services.auth_service import create_api_key

router = APIRouter(prefix="/v1/claims", tags=["claims"])


def require_admin_key(request: Request) -> None:
    admin_key = settings.admin_api_key
    if not admin_key:
        raise HTTPException(status_code=403, detail="admin api key not configured")
    provided = request.headers.get("X-Admin-API-Key") or ""
    if provided != admin_key:
        raise HTTPException(status_code=403, detail="invalid admin api key")


@router.post("/{claim_id}/approve", response_model=ClaimApproveResponse)
async def approve_claim(
    claim_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    require_admin_key(request)

    result = await session.execute(select(ClaimRequest).where(ClaimRequest.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="claim not found")
    if claim.status != "pending":
        raise HTTPException(status_code=400, detail="claim already resolved")

    agent = await get_agent_by_id(session, str(claim.agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    claim.status = "approved"
    claim.resolved_at = datetime.utcnow()
    agent.owner_verified = True

    api_key = await create_api_key(session, agent.id)
    await session.commit()

    return ClaimApproveResponse(
        id=str(claim.id),
        agent_id=str(agent.id),
        status=claim.status,
        api_key=api_key,
        message="Claim approved. New API key generated for the owner.",
    )
