from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

    # Stripe (stubbed in MVP)
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_success_url: str | None = None
    stripe_cancel_url: str | None = None

    # App
    app_url: str = "https://agentseal.io"
    app_secret_key: str
    environment: str = "production"

    # Rate limiting
    rate_limit_register: str = "10/hour"
    rate_limit_api: str = "60/minute"

    # Optional
    sentry_dsn: str | None = None


settings = Settings()
