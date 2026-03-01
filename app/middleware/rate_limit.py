from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


@dataclass
class RateConfig:
    max_requests: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.storage: dict[str, list[float]] = {}

    def allow(self, key: str, config: RateConfig) -> bool:
        now = time.time()
        window_start = now - config.window_seconds
        timestamps = [t for t in self.storage.get(key, []) if t >= window_start]
        if len(timestamps) >= config.max_requests:
            self.storage[key] = timestamps
            return False
        timestamps.append(now)
        self.storage[key] = timestamps
        return True


limiter = InMemoryRateLimiter()


def parse_rate(rate: str) -> RateConfig:
    value, per = rate.split("/")
    value_int = int(value)
    if per == "minute":
        seconds = 60
    elif per == "hour":
        seconds = 3600
    else:
        seconds = 60
    return RateConfig(max_requests=value_int, window_seconds=seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.register_rate = parse_rate(settings.rate_limit_register)
        self.api_rate = parse_rate(settings.rate_limit_api)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/v1/agents":
            ip = request.client.host if request.client else "unknown"
            if not limiter.allow(f"register:{ip}", self.register_rate):
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            api_key = request.headers.get("X-API-Key") or "unknown"
            if not limiter.allow(f"api:{api_key}", self.api_rate):
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

        return await call_next(request)
