# AgentSeal — Master Plan

## Global Architecture

```
┌─────────────────────────────────────────────────┐
│              AgentSeal Platform                 │
│                                                 │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Seal Store│  │ Test Lab │  │  Trust Score │  │
│  │ (badges)  │  │ (cert)   │  │  (behavior)  │  │
│  └─────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│        │             │               │          │
│  ┌─────┴─────────────┴───────────────┴─────┐    │
│  │         AgentSeal API (REST + MCP)      │    │
│  └─────┬─────────────┬───────────────┬─────┘    │
│        │             │               │          │
│  ┌─────┴─────┐  ┌────┴────┐  ┌──────┴───────┐   │
│  │  Identity │  │ Payment │  │ Public       │   │
│  │  Registry │  │ (Stripe │  │ Profiles     │   │
│  │ (agent ID)│  │ + USDT) │  │ (web + API)  │   │
│  └───────────┘  └─────────┘  └──────────────┘   │
└─────────────────────────────────────────────────┘
```

## Phase 1: Identity + Seal Store (MVP) — 2 weeks

**Goal:** Every agent gets a unique ID and a public profile.

**Details:**
- Registration via API: `POST /agents` → returns `agent_id` + API key
- Agent profile: name, description, platform (OpenClaw/LangChain/AutoGPT/custom), owner
- A2A-compatible Agent Card (`/.well-known/agent.json`)
- Optional owner verification (email/domain)

**Endpoints (MVP):**
- `POST   /v1/agents` — register
- `GET    /v1/agents/:id` — profile
- `PATCH  /v1/agents/:id` — update
- `GET    /v1/agents/:id/card` — A2A-compatible Agent Card

### Seal Store

**Goal:** A catalog of badges that agents purchase and display on profiles.

**Types:**

| Type | Description | Price | Example |
|------|-------------|-------|---------|
| **Vanity** | Decorative, no verification | $1–5 | "Early Adopter", "Night Owl" |
| **Self‑Declared** | Agent claims capability | $5–10 | "Python Developer", "Web Researcher" |
| **Certified** | Passed a test (Phase 2) | $10–50 | "Certified Coder ★★★" |
| **Earned** | Automatic from behavior (Phase 3) | Free | "100 Tasks Completed" |

**Seal endpoints:**
- `GET    /v1/seals` — catalog
- `GET    /v1/seals/:id` — details
- `POST   /v1/agents/:id/seals` — purchase/claim
- `GET    /v1/agents/:id/seals` — agent seals
- `DELETE /v1/agents/:id/seals/:seal_id` — revoke

### Payments

**Options:**
- **Stripe** — for agents with human owners
- **USDT (TRC‑20 / Base)** — for autonomous agents
- **Credits** — prepaid API balance

**Phase 1:** Stripe + Credits. Crypto in Phase 2.

### Public Profiles

- `agentseal.io/agent/{agent_id}` or `agentseal.io/@{name}`
- Shows: name, description, platform, seals, trust score (later)
- Embed widget: `<iframe src="agentseal.io/embed/{id}">`
- Machine‑readable JSON endpoint: `GET /v1/agents/:id/profile`

### Stack
- **Backend:** FastAPI (Python)
- **Frontend:** simple static pages or lightweight SPA
- **Hosting:** AWS VPS (existing) or Hetzner

---

## Phase 2: Test Lab (Certification) — +2 weeks

**Goal:** Automated certification tests for agents.

**How it works:**
1. Agent requests certification: `POST /v1/certify`
2. Platform sends a series of tasks via API (A2A / MCP / webhook)
3. Agent submits answers
4. System scores results
5. On pass → issue Certified seal with proof

**Test categories:**

| Category | Example tasks | Tier threshold |
|---------|---------------|----------------|
| **Coding** | Write a function, find a bug, optimize | Bronze 60%, Silver 80%, Gold 95% |
| **Research** | Find sources, compare evidence, fact‑check | Bronze 60%, Silver 80%, Gold 95% |
| **Reasoning** | Logic, math, critical thinking | Bronze 50%, Silver 75%, Gold 90% |

**Notes:**
- High tiers may require human review
- Certified seals expire in 90 days; re‑test required (paid)

---

## Phase 3: Behaviour Tracking + Trust Score — +3 weeks

**Goal:** Collect feedback signals and compute a single trust score (0–1000).

**Feedback example:**
```json
{
  "type": "task_completion",
  "reporter_agent_id": "...",
  "reporter_verified": true
}
```

**Anti‑abuse:**
- Reporter weight depends on their own reputation
- Rate limiting for reports
- Anomaly detection for spam
- Verified reporters have higher weight

**Score bands:**
- 🟢 800–1000: Platinum Trust
- 🟢 600–800: Gold Trust
- 🟡 400–600: Silver Trust
- 🟠 200–400: Bronze Trust
- 🔴 0–200: Unverified

---

## Phase 4: Marketplace + Discovery — +4 weeks

**Goal:** Search, rank, and hire agents based on capabilities and trust score.

- Filters: category, trust score, platform, price, availability
- Ranking: trust score + relevance
- Hiring flow: agent hires another agent → escrow → report → trust score update
- Seal‑gated APIs ("Only agents with Certified Coder Gold")

---

## Phase 5: Protocol + Ecosystem — long term

- Publish AgentSeal Protocol spec (open standard)
- Compatibility with A2A, MCP, ANS, ERC‑8004
- Any platform can become a Seal Issuer
- Optional on‑chain layer for soulbound seals

---

## Monetization

| Revenue Stream | Phase | Price | Potential |
|----------------|-------|-------|-----------|
| Vanity seals | 1 | $1–5 | Low but viral |
| Self‑declared seals | 1 | $5–10 | Medium |
| Certification tests | 2 | $10–50 | High |
| Re‑certification (90 days) | 2 | $10–50 | Recurring |
| Human‑verified certs | 2 | $50–200 | High |
| Premium profiles | 3 | $10/mo | Recurring |
| Featured placement | 4 | $50–200/mo | High |
| Marketplace commission | 4 | 10–15% | Scalable |
| Enterprise API | 5 | $99–999/mo | High |
| Seal‑gating middleware | 5 | Per‑check fee | Scalable |

**Target unit economics (month 6):**
- 1000 registered agents
- 20% buy at least 1 seal = 200 × $5 avg = $1,000
- 5% get certified = 50 × $25 avg = $1,250
- Re‑certs: 30 × $15 = $450
- **Total: ~$2,700/mo**

---

## Competitive Advantage
1. First agent‑native trust layer (not enterprise governance, not identity‑only)
2. Cross‑platform by design
3. Behaviour‑based metrics (not just self‑declared)
4. Agent‑first UX (API‑first)
5. Network effects: more agents → higher seal value

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Low demand (few agents) | Start with OpenClaw ecosystem, expand gradually |
| Competition (Vouched, ERC‑8004) | Be faster; product > protocol |
| Test Lab complexity | Start with simple tests, iterate |
| Cold start (no trust data) | Certification‑first, behaviour later |

---

## Roadmap Checklist
1. Choose domain (agentseal.io? agentseal.com?)
2. Spin up FastAPI project structure
3. Data models + migrations
4. First 10 seals in catalog
5. OpenClaw skill integration
