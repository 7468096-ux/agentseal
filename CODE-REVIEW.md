# Code Review — AgentSeal (Sprint 1 + overall)

Date: 2026-03-01

## Overall architecture
- FastAPI + SQLAlchemy async stack is clean and conventional.
- Routing, services, and models are separated logically.
- Middleware handles auth + rate limiting centrally (good for consistency).

## Strengths
- Clear input validation for names/slugs/platforms.
- Service layer cleanly encapsulates domain logic (issue_seal, create_agent).
- Proper filtering of revoked/expired seals in list and profile endpoints.

## Findings & recommendations

### 1) Configuration & Environment
**Issue:** CORS was hard‑coded and permissive. (Fixed with env‑based config.)
**Recommendation:** Keep all env‑specific config in `Settings`, add documentation to README.

### 2) Error handling & edge cases
- `RateLimitMiddleware` parses `RATE_LIMIT_*` only for `minute` or `hour`. Unexpected values silently fall back to 60 seconds.
  - **Recommendation:** Validate config and raise on invalid values.
- `verify_api_key` loops by prefix and verifies hashes; good for performance but consider logging failed attempts for abuse detection.

### 3) Input validation gaps
- `avatar_url` / `website_url` are strings; should be `HttpUrl` or `AnyUrl` for stricter validation.
- `metadata` size limit exists, but content is not schema‑validated.
  - **Recommendation:** Define a JSON schema if metadata becomes critical.

### 4) Performance & scalability
- In‑memory rate limiter won’t work across multiple instances.
- `get_agent_seals` fetches seals in two queries; could be optimized with a join if performance becomes an issue.

### 5) Type safety & consistency
- Models and schemas are strongly typed, but response dictionaries in `agent_seals` endpoint are untyped dicts.
  - **Recommendation:** Create a response schema for this list for consistency.

### 6) Test coverage
- Tests are minimal (no coverage found for auth/rate limiting/payment/webhooks).
  - **Recommendation:** Add unit tests for:
    - Auth middleware (missing/invalid/expired keys)
    - Rate limiting behavior
    - Issue seal flows (free/paid/invalid)
    - Invite code consumption and exhaustion

## Sprint 1 change review (based on recent updates)
- **Auth via Authorization header:** implemented correctly for write endpoints; ownership check is enforced.
- **Seal filtering for revoked/expired:** enforced in list/profile endpoints and service layer.
- **Protected certification/earned categories:** `issue_seal` correctly blocks purchasing those categories.
- **`proof_hash` field:** present at model layer (verify usage if returned via API).
- **Seed updates:** consistent with categories; ensure seeds stay in sync with business logic.

## Suggested next steps
1. Add webhook signature verification before enabling real payments.
2. Add tests for auth/rate limit/payment flows.
3. Add URL validation types in schemas.
