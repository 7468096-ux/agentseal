from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    # Stripe integration is stubbed for MVP phase 1.
    # Accept the payload and return 200.
    return {"status": "ok"}
