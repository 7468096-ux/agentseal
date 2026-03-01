from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Agent, Payment, Seal


async def create_payment_stub(session: AsyncSession, agent: Agent, seal: Seal) -> Payment:
    checkout_url = f"{settings.app_url}/payment/checkout/{seal.slug}"
    payment = Payment(
        agent_id=agent.id,
        amount_cents=seal.price_cents,
        currency="USD",
        status="pending",
        provider="stripe",
        provider_payment_id=None,
        provider_checkout_url=checkout_url,
    )
    session.add(payment)
    await session.flush()
    return payment


async def mark_payment_completed(session: AsyncSession, payment: Payment) -> None:
    payment.status = "completed"
    payment.completed_at = datetime.utcnow()
