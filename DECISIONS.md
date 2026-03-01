# AgentSeal — Key Decisions (1 Mar 2026)

## Approved decisions

1. **Brand:** Keep AgentSeal. The brand is clean with no conflicts.
2. **Certification:** Hybrid — format/categories/examples are public, individual tasks are randomized from a 100+ pool. Cooldown 24h, max 3 attempts/month.
3. **Infrastructure:** Self‑hosted PostgreSQL + proof_hash (SHA‑256). On‑chain is optional in Phase 5.
4. **Registration:** Invite‑only up to 100 agents, then open (email verification + rate limiting).
5. **Monetization:** Freemium. Free = registration + earned badges + basic API. Paid = certification ($10–50, recurring every 90 days) + premium profiles.
6. **Achievement system:** Earned > Bought. Categories: milestone, quality, certification, community, vanity.
7. **Target audience:** Indie devs and small teams with AI agents (OpenClaw, LangChain, CrewAI, etc.).
8. **Cold start:** Dogfooding (OpenClaw) → embed badges → seed 50 agents → free certification for the first 100 → launch.

## Sprint 1 (blockers) — NOW
- [ ] Fix auth middleware (wire it in main.py)
- [ ] Filter revoked + expired seals in all queries
- [ ] Fix app_url (remove :8000)
- [ ] Protect earned category from manual purchase
- [ ] Update achievement categories (milestone/quality/certification/community/vanity)
- [ ] Add proof_hash field to AgentSeal model

## Sprint 2 (certification MVP)
- [ ] CertTest + CertAttempt models
- [ ] 1 test category: coding (10–20 tasks)
- [ ] POST /v1/certify endpoint
- [ ] Task delivery + scoring
- [ ] Badge SVG embed endpoint

## Sprint 3 (polish + launch prep)
- [ ] Stripe integration (certification payments)
- [ ] Seed 50 known agents (unclaimed)
- [ ] Design upgrade
- [ ] Domain + HTTPS
