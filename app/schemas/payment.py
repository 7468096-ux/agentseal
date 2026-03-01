from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: str
    agent_id: str
    amount_cents: int
    currency: str
    status: str
    provider: str
    provider_payment_id: Optional[str]
    provider_checkout_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
