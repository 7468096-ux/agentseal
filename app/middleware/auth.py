from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.database import AsyncSessionLocal
from app.services.auth_service import verify_api_key


EXEMPT_PATHS = {
    "/v1/agents",
    "/v1/webhooks/stripe",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.url.path in EXEMPT_PATHS and request.method == "POST":
                return await call_next(request)

            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse({"detail": "missing api key"}, status_code=401)

            if auth_header.lower().startswith("bearer "):
                api_key = auth_header.split(" ", 1)[1].strip()
            else:
                api_key = auth_header.strip()

            if not api_key:
                return JSONResponse({"detail": "missing api key"}, status_code=401)

            async with AsyncSessionLocal() as session:
                key = await verify_api_key(session, api_key)
                if not key:
                    return JSONResponse({"detail": "invalid api key"}, status_code=401)
                request.state.agent_id = str(key.agent_id)
                await session.commit()

        return await call_next(request)
