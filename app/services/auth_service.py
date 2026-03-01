from __future__ import annotations

import secrets
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> tuple[str, str, str]:
    raw_key = f"as_live_{secrets.token_hex(16)}"
    key_prefix = raw_key[:8]
    key_hash = pwd_context.hash(raw_key)
    return raw_key, key_prefix, key_hash


async def create_api_key(session: AsyncSession, agent_id: str) -> str:
    raw_key, prefix, key_hash = generate_api_key()
    api_key = ApiKey(agent_id=agent_id, key_hash=key_hash, key_prefix=prefix)
    session.add(api_key)
    await session.flush()
    return raw_key


async def verify_api_key(session: AsyncSession, raw_key: str) -> ApiKey | None:
    if not raw_key or len(raw_key) < 8:
        return None
    prefix = raw_key[:8]
    result = await session.execute(select(ApiKey).where(ApiKey.key_prefix == prefix))
    api_keys = result.scalars().all()
    for api_key in api_keys:
        if not api_key.is_active:
            continue
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            continue
        if pwd_context.verify(raw_key, api_key.key_hash):
            api_key.last_used_at = datetime.utcnow()
            return api_key
    return None
