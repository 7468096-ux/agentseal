from __future__ import annotations

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Agent

router = APIRouter(prefix="/v1/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/github")
async def github_login(agent_id: str = Query(...)):
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": f"{settings.app_url}/v1/auth/github/callback",
        "scope": "read:user",
        "state": agent_id,
    }
    return RedirectResponse(url=f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}")


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    agent_id = state
    result = await session.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": f"{settings.app_url}/v1/auth/github/callback",
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub token exchange failed")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="GitHub did not return access token")

        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub user fetch failed")

        github_user = user_resp.json()

    github_username = github_user.get("login")
    if not github_username:
        raise HTTPException(status_code=502, detail="GitHub username not available")

    agent.github_username = github_username
    agent.github_verified = True
    await session.commit()

    return RedirectResponse(url=f"{settings.app_url}/@{agent.slug}", status_code=302)
