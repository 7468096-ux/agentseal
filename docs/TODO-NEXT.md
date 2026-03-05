# AgentSeal MVP — TODO

## ✅ Done
- [x] FastAPI project created
- [x] All SQLAlchemy models (agents, api_keys, seals, agent_seals, payments, invite_codes)
- [x] Docker Compose (app + postgres) on VPS 54.254.155.94:8000
- [x] Tables auto‑created on startup (create_all)
- [x] API responds (GET /v1/seals returns an empty catalog)

## 🔴 Next (priority)
1. [x] Run seed.py inside the Docker container (16 seals + Alice + 5 invite codes)
2. [x] Verify all endpoints: POST /v1/agents, GET /v1/agents/:id, GET /v1/seals, POST /v1/agents/:id/seals
3. [x] Fix bugs as found (passlib/bcrypt incompatibility → pin bcrypt==3.2.2)
4. [x] Landing page (GET /) — verify it renders
5. [x] Profile page (GET /@slug) — verify
6. [x] Caddy reverse proxy (80/443) + AWS SG ports opened — http://54.254.155.94 works

## 🧪 Checks (27 Feb)
- POST /v1/agents requires invite_code (invite‑only).
- POST /v1/agents (with invite) → 201 + api_key.
- GET /v1/agents/:id → OK.
- GET /v1/seals → 16 seals.
- POST /v1/agents/:id/seals (paid) → payment_required + checkout_url (stub).

## 🧪 Checks (28 Feb)
- Seed confirmed: /v1/seals returns 16 seals.
- POST /v1/agents (invite_98ca1cd0faa62a5f) → 201 + api_key.
- GET /v1/agents/:id + /by-slug → OK.
- GET /v1/agents/:id/seals → registered seal.
- POST /v1/agents/:id/seals (early-adopter) → payment_required + checkout_url.
- HTML pages: / and /@test-agent-1 → 200.
- External access to 54.254.155.94:8000 from local machine hangs (port/SG likely closed).

## 🧪 Checks (01 Mar)
- GET /v1/seals → OK (catalog with 16 seals).
- POST /v1/agents (invite_a1a457cc34233553) → 201 + api_key (agent: test-agent-2).
- GET /v1/agents/:id + /by-slug/test-agent-2 → OK.
- GET /v1/agents/:id/seals → registered seal.
- POST /v1/agents/:id/seals (early-adopter) → payment_required + checkout_url.
- HTML pages: / and /@test-agent-2 → 200.
- External access to 54.254.155.94:8000 still hangs (port/SG closed).

## 🟡 Later
- [ ] Buy domain agentseal.io
- [ ] Configure Caddy + HTTPS
- [ ] GitHub repo for CI/CD
- [ ] Tests with a real DB

## Deploy
