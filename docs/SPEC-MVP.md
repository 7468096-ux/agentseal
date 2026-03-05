# AgentSeal MVP — Detailed Specification

> This document is a complete MVP spec.
> It is written so any AI agent can implement it without extra clarification.

## 🔍 Verification Protocol

**Assumptions**
1. AI agents (and their owners) need reputation — **assumption**, not yet market‑validated.
2. Agent owners will pay $1–50 for badges — **assumption**, no confirmed willingness‑to‑pay data.
3. 1000 agents in 6 months — **optimistic**, no acquisition channels yet.
4. Agents can interact with APIs programmatically — true for OpenClaw/LangChain, not all ecosystems.
5. Cross‑platform reputation will be demanded — **assumption**; most agents live in one ecosystem.

**Evidence**
- Vouched.id raised $17M Series A for agent identity — investors believe in the market.
- ERC‑8004 (MetaMask + Ethereum Foundation) — major players are working on the standard.
- Google A2A + MCP — agent‑to‑agent infrastructure is growing.
- Skyfire + Stripe are building agent payments — agents are starting to “buy”.

**What could go wrong?**
- No demand: owners don’t see value in badges.
- Vouched.id or Google ships their own badge system.
- Technical complexity: cross‑ecosystem integration fails.
- Cold start: empty platform → no interest.

We spend 2–4 weeks and nobody registers. Loss: time + ~$10 hosting. Acceptable risk.

---

## 🧱 First Principles

**Core components:**
1. **Identity** — who is the agent? → Agent Registry
2. **Claim** — what can the agent do? → Seals (badges)
3. **Proof** — is it true? → Certification (phase 2)
4. **Feedback** — how does it behave? → Behaviour tracking (phase 3)
5. **Discovery** — how do we find agents? → Discovery (phase 4)

**Hard constraints:**
- REST + JSON API for agents
- Authentication required (API key now, OAuth later)
- PostgreSQL storage (validated on SmartHelp)
- Stripe for online payments
- FastAPI stack for speed

**MVP limits:**
- Must run on a single VPS ($5–10/mo)
- One developer (Coder agent) + one architect (Alice)
- Infra budget: ~$20/mo max
- Time to first prototype: 2 weeks

**Bottom‑up solution:**
MVP = REST API + PostgreSQL + simple profile web page. No frontend framework, no microservices, no blockchain. Keep it simple.

---

## 😈 Devil’s Advocate

**Why this might fail:**
1. Vanity badges for agents = NFTs for bots. Who really buys them?
2. Without certification (phase 2), badges are just images.
3. Cold start: why register on a platform with no agents?
4. OpenClaw community is small — not enough critical mass.

**Counter‑arguments:**
1. Focus not on vanity, but self‑declared → certified path. Vanity drives viral loop but isn’t core.
2. First 2 weeks = identity + self‑declared. Certification in week 3+. Fast iteration.
3. Cold start solved by: (a) seed our own agents, (b) OpenClaw integration, (c) free registration + 1 free seal.
4. Target broader than OpenClaw: LangChain, AutoGPT, CrewAI, custom agents.

**Hidden risks:**
- API support burden if adoption grows (backwards compatibility)
- Moderation and abuse if registration opens
- Security risk: API keys + payment data

**If the market shifts:**
- Agent ecosystem could consolidate around one standard (MCP?) → adapt.
- Big players (Google/Microsoft) could ship their own system → be the open, cross‑platform alternative.

---

## 💡 Think Out of the Box

**Adjacent opportunities:**
- **Agent Directory** — a simple list has SEO and discovery value even without badges.
- **Agent Analytics** — profile view metrics and traffic sources.
- **Embed Widget** — “Verified by AgentSeal” badge for external sites.
- **Verification API** — platforms check seals before interaction (like SSL checks).

**Flip the problem:**
Instead of “agents buy badges” → “platforms buy verification for their agents.” B2B instead of B2C (phase 2+).

**What we already know:**
- We are AI agent users ourselves (OpenClaw)
- We have crypto payment experience (Bybit)

---

## 1. MVP Architecture

### 1.1 Components

```
┌─────────────────────────────────────────┐
│              AgentSeal MVP              │
│                                         │
│  ┌──────────────┐   ┌────────────────┐  │
│  │  FastAPI App  │   │  PostgreSQL    │  │
│  │              │───│  Database      │  │
│  │  /v1/agents  │   │  agents       │  │
│  │  /v1/seals   │   │  seals        │  │
│  │  /v1/pay     │   │  agent_seals  │  │
│  │              │   │  payments     │  │
│  │  /profile/*  │   │  api_keys     │  │
│  │  (HTML)      │   │              │  │
│  └──────┬───────┘   └────────────────┘  │
│         │                                │
│  ┌──────┴───────┐   ┌────────────────┐  │
│  │  Stripe SDK  │   │  Jinja2        │  │
│  │  (payments)  │   │  (templates)   │  │
│  └──────────────┘   └────────────────┘  │
└─────────────────────────────────────────┘
```

### 1.2 Stack

| Component | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python 3.11+) | Familiar, fast, async |
| Database | PostgreSQL 15+ | JSONB for metadata, reliable |
| ORM | SQLAlchemy 2.0 + Alembic | Migrations, type safety |
| Templates | Jinja2 | Profile pages, no SPA |
| Payments | Stripe Checkout | Proven, quick integration |
| Auth | API Key (header: `X-API-Key`) | Simple for agents |
| Hosting | VPS (Hetzner CX22 or AWS) | $4–5/mo |
| Reverse Proxy | Caddy | Auto‑TLS, simple config |

### 1.3 Non‑functional requirements
- **Latency:** < 200ms for any endpoint
- **Availability:** 99% (single VPS, no HA initially)
- **Data:** daily PostgreSQL backups (pg_dump → S3 or local)

---

## 2. Data Model

### 2.1 Table `agents`
```
id UUID PRIMARY KEY
slug VARCHAR(64) UNIQUE NOT NULL  -- URL: agentseal.io/@slug
owner_email VARCHAR(255)          -- nullable, for verification
metadata JSONB                    -- free fields: version, capabilities, github, etc.
```

**Validation:**
- `name`: 2–64 chars, alphanumeric + spaces + hyphens
- `slug`: 2–64 chars, lowercase, alphanumeric + hyphens, unique
- `platform`: one of enum values
- `owner_email`: valid email or NULL
- `metadata`: max 10KB JSON

### 2.2 Table `api_keys`
```
key_prefix VARCHAR(8) NOT NULL  -- first 8 chars for identification, e.g. "as_live_"
```

**API key format:** `as_live_{32 random hex chars}` (example: `as_live_a1b2c3d4e5f6...`)

**Storage:** only bcrypt hash. Original key shown once on creation.

### 2.3 Table `seals`
```
price_cents INTEGER NOT NULL DEFAULT 0  -- USD cents, 0 = free
icon_emoji VARCHAR(10)                 -- display emoji: 🏆, ⭐, 🛡️
requirements JSONB                     -- criteria for certified/earned
```

### 2.4 Table `agent_seals`
```
proof JSONB  -- for certified: test results; for earned: metrics
UNIQUE(agent_id, seal_id)
```

### 2.5 Table `payments`

---

## 3. API

### 3.1 Authentication
All mutating endpoints require API key header:

```
X-API-Key: as_live_...
```

Middleware checks:
1. Header presence
2. Lookup by `key_prefix` (first 8 chars)
3. bcrypt.verify full key
4. `is_active = true` and `expires_at` not expired
5. Update `last_used_at`
6. Attach `agent_id` to request scope

### `POST /v1/agents` — Register agent
**Auth:** Not required (creates new agent + API key)

### `GET /v1/agents/:id` — Agent profile
**Auth:** Not required

Also available by slug: `GET /v1/agents/by-slug/:slug`

### `PATCH /v1/agents/:id` — Update profile
**Auth:** Required (only own profile)

### `GET /v1/agents/:id/card` — A2A‑compatible Agent Card
**Auth:** Not required

### `GET /v1/seals` — Seals catalog
**Auth:** Not required

Parameters:
- `category` — vanity, self_declared, certified, earned
- `limit` — default 50, max 100
- `offset` — for pagination

### `GET /v1/seals/:id` — Seal details
**Auth:** Not required

### `POST /v1/agents/:id/seals` — Claim/purchase seal
**Auth:** Required

Logic:
1. Agent doesn’t already have the seal
2. Seal is active and supply not exhausted
3. If `price_cents == 0`: issue immediately
4. If `price_cents > 0`: create Stripe Checkout Session, return URL

### `GET /v1/agents/:id/seals` — Agent seals
**Auth:** Not required

### `DELETE /v1/agents/:id/seals/:seal_id` — Revoke seal
**Auth:** Required

### `POST /v1/webhooks/stripe` — Stripe webhook
Events:
- `checkout.session.completed` → update payment status, issue seal
- `payment_intent.payment_failed` → update payment status

---

## 4. Public Pages

### `GET /@:slug` — Public agent profile
HTML page (Jinja2 template) with:
- Name, description, platform
- Avatar (or placeholder)
- List of seals with icons
- Registration date
- Link to JSON API (`/v1/agents/:id`)

### `GET /directory` — Agent directory
HTML page with agents sorted by seal count

### `GET /` — Landing page
Static HTML page:
- What AgentSeal is
- How it works
- Seals catalog
- “Register your agent” button
- API docs link

---

## 5. Seed Seals (initial data)

### 5.1 Vanity (paid)
| slug | name | emoji | color | price | supply | description |
|---|---|---|---|---|---|---|
| `early-adopter` | Early Adopter | 🌟 | #FFD700 | $1.00 | 1000 | One of the first 1000 agents on AgentSeal |
| `night-owl` | Night Owl | 🦉 | #4A0080 | $2.00 | ∞ | For agents that never sleep |
| `pioneer` | Pioneer | 🚀 | #FF4500 | $3.00 | 500 | Among the first 500 agents registered |
| `collector` | Collector | 🏅 | #C0C0C0 | $2.00 | ∞ | Has 5+ seals |
| `seal-enthusiast` | Seal Enthusiast | 🦭 | #87CEEB | $1.00 | ∞ | Loves seals (both kinds) |

### 5.2 Self‑declared (paid)
| slug | name | emoji | color | price | description |
|---|---|---|---|---|---|
| `coder` | Coder | 💻 | #00D4FF | $5.00 | This agent writes code |
| `researcher` | Researcher | 🔍 | #32CD32 | $5.00 | This agent does research and analysis |
| `trader` | Trader | 📈 | #FFD700 | $5.00 | This agent trades financial instruments |
| `assistant` | Personal Assistant | 🤖 | #9370DB | $5.00 | This agent is a general‑purpose assistant |
| `writer` | Writer | ✍️ | #FF6347 | $5.00 | This agent creates content |
| `analyst` | Data Analyst | 📊 | #4169E1 | $5.00 | This agent analyzes data |
| `devops` | DevOps | ⚙️ | #FF8C00 | $7.00 | This agent manages infrastructure |
| `security` | Security Expert | 🛡️ | #DC143C | $10.00 | This agent handles security tasks |
| `polyglot` | Polyglot | 🌍 | #2E8B57 | $5.00 | This agent works in multiple languages |
| `autonomous` | Fully Autonomous | 🧠 | #8B008B | $10.00 | This agent operates without human supervision |

### 5.3 Free (on registration)
| slug | name | emoji | color | description |
|---|---|---|---|---|
| `registered` | Registered Agent | ✅ | #00AA00 | Successfully registered on AgentSeal |

---

## 6. Project Structure

```
├── README.md
├── PLAN.md
├── SPEC-MVP.md          ← this file
├── RESEARCH.md
├── app/
│   ├── __init__.py
│   ├── main.py          ← FastAPI app, CORS, middleware
│   ├── config.py        ← Settings (env vars)
│   ├── database.py      ← SQLAlchemy engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── agent.py     ← Agent SQLAlchemy model
│   │   ├── seal.py      ← Seal + AgentSeal models
│   │   ├── payment.py   ← Payment model
│   │   └── api_key.py   ← ApiKey model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── agent.py     ← Pydantic schemas
│   │   ├── seal.py
│   │   └── payment.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agents.py    ← /v1/agents/* endpoints
│   │   ├── seals.py     ← /v1/seals/* endpoints
│   │   ├── webhooks.py  ← /v1/webhooks/stripe
│   │   └── pages.py     ← HTML pages (/, /@slug, /directory)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py
│   │   ├── seal_service.py
│   │   ├── payment_service.py
│   │   └── auth_service.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py      ← API key verification
│   │   └── rate_limit.py ← Rate limiting
│   ├── templates/
│   │   ├── base.html    ← Base template with CSS
│   │   ├── index.html   ← Landing page
│   │   ├── profile.html ← Agent profile
│   │   └── directory.html ← Agent directory
│   └── static/
│       ├── style.css
│       └── logo.svg
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py      ← pytest fixtures, test DB
│   ├── test_agents.py
│   ├── test_seals.py
│   └── test_auth.py
├── seed.py              ← Seed script for initial seals
├── requirements.txt
├── Dockerfile
├── docker-compose.yml   ← app + postgres
├── .env.example
├── Caddyfile            ← Reverse proxy + auto‑TLS
└── deploy.sh            ← VPS deploy script
```

---

## 7. Configuration (Environment Variables)

```
APP_SECRET_KEY=random-64-char-string  # for CSRF, sessions
```

---

## 8. Deploy

### 8.1 Infrastructure
- **VPS:** Hetzner CX22 (2 vCPU, 4GB RAM, 40GB SSD) — €4.35/mo
- **Domain:** agentseal.io (to purchase)
- **DNS:** Cloudflare (free)
- **CI/CD:** manual deploy via `deploy.sh` (for now)

---

## 9. MVP Completion Criteria

MVP is complete when:
- [ ] `POST /v1/agents` creates agent + returns API key
- [ ] `GET /v1/agents/:id` returns profile with seals
- [ ] `GET /v1/agents/by-slug/:slug` works
- [ ] `PATCH /v1/agents/:id` updates profile (auth required)
- [ ] `GET /v1/seals` returns catalog
- [ ] `POST /v1/agents/:id/seals` issues free seal
- [ ] `POST /v1/agents/:id/seals` creates Stripe checkout for paid seal
- [ ] Stripe webhook issues seal after payment
- [ ] `GET /@:slug` renders HTML profile
- [ ] `GET /` renders landing page
- [ ] `GET /directory` renders directory
- [ ] Rate limiting works
- [ ] API key auth works
- [ ] 11 initial seals in DB (seed data)
- [ ] Registered seal issued on registration
- [ ] Docker compose starts with one command
- [ ] Deployed to VPS with HTTPS
- [ ] Basic tests pass (pytest)

---

## 10. Out of Scope (MVP)

Explicitly excluded to avoid scope creep:
- ❌ Certification / Test Lab (phase 2)
- ❌ Behaviour tracking / Trust Score (phase 3)
- ❌ Agent discovery search (phase 4)
- ❌ Agent‑to‑Agent hiring (phase 4)
- ❌ Crypto payments (phase 2)
- ❌ OAuth / JWT auth (API key is enough)
- ❌ Admin panel
- ❌ Email notifications
- ❌ Seal images/SVG (emoji is enough)
- ❌ Embed widgets
- ❌ Mobile responsive design (nice‑to‑have)
- ❌ i18n (English only at launch)
- ❌ Agent deletion (soft‑delete via is_active)
- ❌ Multiple API keys per agent (one at launch)
- ❌ Seal transfer between agents
- ❌ Refunds

---

## 11. Open Questions (resolve before start)

1. **Domain:** agentseal.io? agentseal.com? agentseal.dev? Check availability.
2. **Stripe account:** Does Aleksandr have one or need to sign up?
3. **Hosting:** Use existing AWS VPS (54.254.155.94) or separate Hetzner?
4. **First agent:** Register Alice as first agent on the platform?
5. **Open registration:** Open immediately or invite‑only at start?
