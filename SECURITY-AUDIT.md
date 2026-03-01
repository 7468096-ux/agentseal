# Security Audit — AgentSeal

Date: 2026-03-01
Scope: Full codebase under `app/` + configuration files + dependencies

## Summary
- **Critical/High fixed:** CORS misconfiguration (wildcard origins + credentials). Now configurable via env, with credentials off by default.
- Other findings are MEDIUM/LOW with recommended remediations below.

## Findings

### HIGH — CORS misconfiguration (fixed)
**Location:** `app/main.py`

**Issue:** `allow_origins=["*"]` combined with `allow_credentials=True` allows any origin to make credentialed requests. If API keys are ever stored in a browser context, this can enable cross‑origin abuse.

**Fix applied:** CORS is now configured via environment variables with a safe default and credentials disabled by default.

**Recommendation:**
- Set `CORS_ALLOW_ORIGINS` to the trusted frontend domain(s) only.
- Keep `CORS_ALLOW_CREDENTIALS=false` unless you explicitly use cookies.

---

### MEDIUM — Webhook endpoint lacks signature verification
**Location:** `app/routers/webhooks.py`

**Issue:** `/v1/webhooks/stripe` currently accepts any payload without validating Stripe signatures. If this endpoint later triggers state changes, it can be abused.

**Recommendation:**
- Implement Stripe signature verification using `STRIPE_WEBHOOK_SECRET` before enabling real payment flows.
- Reject invalid signatures with 400.

---

### MEDIUM — Rate limiting is in‑memory only
**Location:** `app/middleware/rate_limit.py`

**Issue:** In‑memory rate limiting is per‑process. Horizontal scaling or restarts reset counters and allow abuse.

**Recommendation:**
- Move rate limiting to a shared store (Redis) or API gateway.
- Add separate limits for sensitive endpoints (e.g., webhooks, login if added).

---

### LOW — Secrets stored in local `.env.production`
**Location:** `.env.production` (local only; ignored by git)

**Issue:** The file contains real secrets. While it is git‑ignored, it should be handled carefully to avoid accidental exposure.

**Recommendation:**
- Store production secrets in a secret manager (AWS SSM/Secrets Manager, Doppler, etc.).
- Rotate any secrets that might have been exposed.

---

### LOW — Minimal validation for URLs
**Location:** `app/schemas/agent.py`

**Issue:** `avatar_url` and `website_url` are plain strings, not URL types. This is not directly exploitable but can lead to inconsistent data.

**Recommendation:**
- Use `AnyUrl`/`HttpUrl` from Pydantic for URL validation.

## Dependency review
`requirements.txt` contains pinned versions. No automated vulnerability scan was available in this environment; consider running `pip-audit` or `safety` in CI.

## Notes
- No direct SQL injection vectors were identified (SQLAlchemy ORM used with parameters).
- Auth checks are enforced for write operations and ownership is verified for updates/issuance.
