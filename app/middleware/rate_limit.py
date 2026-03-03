"""
Rate limiting middleware for AgentSeal.

Limits:
- Default: 100 requests/minute per IP
- Registration: 5/hour per IP
- Behaviour reports: 20/hour per key/IP
- Certification attempts: 10/hour per key/IP
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from fastapi import Request
from fastapi.responses import JSONResponse


def _get_api_key_or_ip(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "")
    if auth.startswith("Bearer "):
        return f"key:{auth[7:][:16]}"
    if api_key:
        return f"key:{api_key[:16]}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_get_api_key_or_ip,
    default_limits=["100/minute"],
    storage_uri="memory://",
)


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after_seconds": 60,
        },
    )


class RateLimitMiddleware(SlowAPIMiddleware):
    """Thin wrapper so main.py can add_middleware(RateLimitMiddleware)."""
    pass


def setup_rate_limiting(app):
    """Alternative: attach rate limiting to the FastAPI application."""
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
