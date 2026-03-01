# AgentSeal MVP — TODO

## ✅ Done
- [x] FastAPI проект создан
- [x] Все модели SQLAlchemy (agents, api_keys, seals, agent_seals, payments, invite_codes)
- [x] Schemas, routers, services
- [x] Docker Compose (app + postgres) на VPS 3.0.92.255:8000
- [x] Таблицы создаются автоматически (create_all на startup)
- [x] API отвечает (GET /v1/seals возвращает пустой каталог)

## 🔴 Next (по приоритету)
1. [x] Запустить seed.py внутри Docker контейнера (16 значков + Alice + 5 invite codes)
2. [x] Проверить все endpoints: POST /v1/agents, GET /v1/agents/:id, GET /v1/seals, POST /v1/agents/:id/seals
3. [x] Фиксить баги по ходу (passlib/bcrypt incompatibility → pin bcrypt==3.2.2)
4. [x] Landing page (GET /) — проверить что рендерится
5. [x] Profile page (GET /@slug) — проверить
6. [x] Caddy reverse proxy (80/443) + AWS SG ports opened — http://3.0.92.255 работает

## 🧪 Проверки (27 Feb)
- POST /v1/agents требует invite_code (invite-only). 
- POST /v1/agents (with invite) → 201 + api_key.
- GET /v1/agents/:id → OK.
- GET /v1/seals → 16 seals.
- POST /v1/agents/:id/seals (paid) → payment_required + checkout_url (stub).

## 🧪 Проверки (28 Feb)
- Seed подтверждён: /v1/seals возвращает 16 seals.
- POST /v1/agents (invite_98ca1cd0faa62a5f) → 201 + api_key.
- GET /v1/agents/:id + /by-slug → OK.
- GET /v1/agents/:id/seals → registered seal.
- POST /v1/agents/:id/seals (early-adopter) → payment_required + checkout_url.
- HTML pages: / и /@test-agent-1 → 200.
- Внешний доступ к 3.0.92.255:8000 с локальной машины зависает (вероятно закрыт порт в SG/Firewall).

## 🧪 Проверки (01 Mar)
- GET /v1/seals → OK (каталог с 16 seals).
- POST /v1/agents (invite_a1a457cc34233553) → 201 + api_key (agent: test-agent-2).
- GET /v1/agents/:id + /by-slug/test-agent-2 → OK.
- GET /v1/agents/:id/seals → registered seal.
- POST /v1/agents/:id/seals (early-adopter) → payment_required + checkout_url.
- HTML pages: / и /@test-agent-2 → 200.
- Внешний доступ к 3.0.92.255:8000 всё ещё зависает (порт/SG закрыт).

## 🟡 Later
- [ ] Купить домен agentseal.io
- [ ] Настроить Caddy + HTTPS
- [ ] GitHub repo для CI/CD
- [ ] Тесты с реальной БД

## Деплой
```bash
cd projects/agent-reputation
tar czf /tmp/agentseal.tar.gz --exclude=__pycache__ --exclude=.git .
scp -i ~/.ssh/crypto-bot.pem /tmp/agentseal.tar.gz ubuntu@3.0.92.255:/tmp/
ssh -i ~/.ssh/crypto-bot.pem ubuntu@3.0.92.255 "cd /opt/agentseal && tar xzf /tmp/agentseal.tar.gz && docker compose up -d --build"
```

## Seed
```bash
ssh -i ~/.ssh/crypto-bot.pem ubuntu@3.0.92.255 "docker compose -f /opt/agentseal/docker-compose.yml exec app python seed.py"
```
