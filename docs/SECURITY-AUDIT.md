# Security Audit — AgentSeal

Date: 2026-03-02
Scope: Full codebase under `app/` + configuration files + dependencies (Sprint 4 additions included)

## Summary
- **High fixed:** Certification attempt re-submission allowed score gaming. Now blocked after first submit.
- **High fixed (prior):** CORS misconfiguration (wildcard origins + credentials). Now configurable via env, with credentials off by default.
- Other findings are MEDIUM/LOW with recommended remediations below.

## Findings

### HIGH — Certification attempt can be re-submitted (fixed)
**Location:** `app/routers/certification.py`

**Issue:** `/v1/attempts/{attempt_id}/submit` accepted multiple submissions, letting users iterate answers until they pass and effectively bypassing assessment integrity.

**Fix applied:** Reject submissions when `attempt.status == "completed"`.

**Recommendation:**
- Consider locking attempts server-side and adding an idempotency token if retry behavior is needed.

---

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

---

### MEDIUM — Public report endpoint has limited rate limiting
**Location:** `app/routers/behaviour.py` (`/v1/agents/{agent_id}/public-report`)

**Issue:** Rate limiting is enforced only per email (5/day) and bypassable with disposable emails. The global in‑memory rate limiter does not apply to this form.

**Recommendation:**
- Add IP‑based or user‑agent throttling (ideally shared store / gateway).
- Consider CAPTCHA for public submissions.

---

### LOW — Public report comment size is unbounded
**Location:** `app/routers/behaviour.py`

**Issue:** `comment` is stored in JSON `details` without length limits; could lead to oversized payloads or DB bloat.

**Recommendation:**
- Add a max length (e.g., 1–2k chars) and reject or truncate.

---

### LOW — Public report content not normalized beyond trimming
**Location:** `app/routers/behaviour.py`

**Issue:** Comment is stored as raw text; currently not rendered, but if surfaced later it could enable stored XSS if not escaped.

**Recommendation:**
- Keep Jinja auto‑escaping on any future rendering; consider sanitizing or encoding now.

---

### MEDIUM — Claim submission can be spammed
**Location:** `app/routers/agents.py` (`POST /v1/agents/{agent_id}/claim`)

**Issue:** Anyone can submit claims for any unverified agent with no rate limiting or verification. This does not grant ownership (admin approval required), but can spam storage and operational queues.

**Recommendation:**
- Add IP/email rate limits and CAPTCHA.
- Consider blocking duplicate pending claims per agent/email.

---

### LOW — Certification cooldown/limit can be bypassed via multiple in‑progress attempts
**Location:** `app/services/certification_service.py`

**Issue:** Cooldown is enforced only after a completed attempt; agents can create many in‑progress attempts to sample tasks.

**Recommendation:**
- Enforce a single in‑progress attempt per agent/test, or mark started attempts toward monthly limits.

## Dependency review
`requirements.txt` contains pinned versions. No automated vulnerability scan was available in this environment; consider running `pip-audit` or `safety` in CI.

## Notes
- No direct SQL injection vectors were identified (SQLAlchemy ORM used with parameters).
- Auth checks are enforced for write operations and ownership is verified for updates/issuance.
