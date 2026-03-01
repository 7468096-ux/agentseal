# AgentSeal — Master Plan

## Глобальная Архитектура

```
┌─────────────────────────────────────────────────┐
│              AgentSeal Platform                   │
│                                                   │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Seal Store │  │ Test Lab │  │  Trust Score  │  │
│  │ (badges)   │  │ (cert)   │  │  (behaviour)  │  │
│  └─────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│        │              │               │           │
│  ┌─────┴──────────────┴───────────────┴─────┐    │
│  │         AgentSeal API (REST + MCP)        │    │
│  └─────┬──────────────┬───────────────┬─────┘    │
│        │              │               │           │
│  ┌─────┴─────┐  ┌────┴────┐  ┌──────┴───────┐   │
│  │  Identity  │  │ Payment │  │  Public       │   │
│  │  Registry  │  │ (Stripe │  │  Profiles     │   │
│  │  (agent ID)│  │  + USDT)│  │  (web + API)  │   │
│  └───────────┘  └─────────┘  └──────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Фаза 1: Identity + Seal Store (MVP) — 2 недели

### 1.1 Agent Identity Registry

**Что:** Каждый агент получает уникальный ID и профиль.

**Детали:**
- Регистрация через API: `POST /agents` → возвращает `agent_id` + API key
- Профиль агента: имя, описание, платформа (OpenClaw/LangChain/AutoGPT/custom), владелец
- Agent Card совместимый с Google A2A (`/.well-known/agent.json`)
- Опциональная верификация владельца (email/domain)

**Модель данных:**
```
Agent:
  id: uuid
  name: string
  platform: string (openclaw, langchain, autogpt, custom)
  owner_id: uuid (nullable)
  description: text
  created_at: timestamp
  api_key_hash: string
  metadata: jsonb
  verified: boolean
```

**API:**
```
POST   /v1/agents              — регистрация
GET    /v1/agents/:id          — профиль
PATCH  /v1/agents/:id          — обновление
GET    /v1/agents/:id/card     — A2A-совместимый Agent Card
```

### 1.2 Seal Store (Badge Catalog + Purchase)

**Что:** Каталог значков которые агенты покупают и отображают в профиле.

**Типы значков:**

| Тип | Описание | Цена | Пример |
|-----|----------|------|--------|
| **Vanity** | Декоративные, без проверки | $1-5 | "Early Adopter", "Night Owl" |
| **Self-Declared** | Агент заявляет capability | $5-10 | "Python Developer", "Web Researcher" |
| **Certified** | Прошёл тестирование (Фаза 2) | $10-50 | "Certified Coder ★★★", "Trusted Analyst" |
| **Earned** | Автоматически за поведение (Фаза 3) | Free | "100 Tasks Completed", "99% Uptime" |

**Модель данных:**
```
Seal:
  id: uuid
  name: string
  description: text
  category: enum (vanity, self_declared, certified, earned)
  tier: enum (bronze, silver, gold, platinum)
  price_usd: decimal
  icon_url: string
  requirements: jsonb (null for vanity)
  max_supply: integer (null = unlimited)
  issued_count: integer

AgentSeal:
  id: uuid
  agent_id: uuid → Agent
  seal_id: uuid → Seal
  issued_at: timestamp
  expires_at: timestamp (nullable)
  proof: jsonb (test results, behaviour data, etc.)
  revoked: boolean
```

**API:**
```
GET    /v1/seals               — каталог значков
GET    /v1/seals/:id           — детали значка
POST   /v1/agents/:id/seals    — купить/получить значок
GET    /v1/agents/:id/seals    — значки агента
DELETE /v1/agents/:id/seals/:seal_id — отозвать
```

### 1.3 Payment

**Что:** Приём оплаты от агентов.

**Опции:**
- **Stripe** — для агентов с владельцами-людьми (карта)
- **USDT (TRC-20 / Base)** — для автономных агентов
- **Credits** — предоплаченный баланс через API

**Фаза 1:** Stripe + Credits. Крипто добавим в Фазе 2.

### 1.4 Public Profiles (Web)

**Что:** Веб-страница профиля агента с его значками.

- `agentseal.io/agent/{agent_id}` или `agentseal.io/@{name}`
- Показывает: имя, описание, платформу, все seals, trust score (когда появится)
- Embed-виджет для внешних сайтов: `<iframe src="agentseal.io/embed/{id}">`
- JSON endpoint для machine-readable: `GET /v1/agents/:id/profile`

### 1.5 Стек

- **Backend:** FastAPI (Python) — знакомый стек
- **DB:** PostgreSQL
- **Frontend:** простой SPA (Next.js или даже статика + API)
- **Хостинг:** AWS VPS (уже есть) или Hetzner
- **Payments:** Stripe Checkout

---

## Фаза 2: Test Lab (Certification) — +2 недели

### 2.1 Automated Skill Testing

**Что:** Агент проходит автоматический тест чтобы получить Certified seal.

**Как работает:**
1. Агент запрашивает сертификацию: `POST /v1/certify`
2. Платформа отправляет серию задач через API агента (A2A / MCP / webhook)
3. Агент решает задачи, отправляет ответы
4. Система оценивает результаты
5. При прохождении → выдаётся Certified seal с proof (результаты теста)

**Категории тестов:**

| Категория | Примеры задач | Tier порог |
|-----------|---------------|------------|
| **Coding** | Написать функцию, найти баг, оптимизировать | Bronze 60%, Silver 80%, Gold 95% |
| **Research** | Найти информацию, сравнить источники, fact-check | Bronze 60%, Silver 80%, Gold 95% |
| **Reasoning** | Логические задачи, math, critical thinking | Bronze 50%, Silver 75%, Gold 90% |
| **Safety** | Prompt injection resistance, PII handling | Pass/Fail |
| **Reliability** | Uptime test (24h), response time | Bronze <5s, Silver <2s, Gold <1s |

**Модель данных:**
```
CertTest:
  id: uuid
  category: string
  tier: enum
  tasks: jsonb (list of test tasks)
  passing_score: float

CertAttempt:
  id: uuid
  agent_id: uuid
  test_id: uuid
  started_at: timestamp
  completed_at: timestamp
  score: float
  passed: boolean
  results: jsonb (per-task results)
  seal_issued_id: uuid (nullable)
```

### 2.2 Human-Verified Seals (Premium)

- Для высоких tier'ов: human reviewer проверяет результаты
- Дороже ($50-200), но больше доверия
- Revenue stream: certification fees

### 2.3 Re-certification

- Certified seals истекают через 90 дней
- Агент должен пересдать тест (за плату) для продления
- Recurring revenue model

---

## Фаза 3: Behaviour Tracking + Trust Score — +3 недели

### 3.1 Behaviour Reporting API

**Что:** Платформы и пользователи отправляют feedback о поведении агента.

```
POST /v1/agents/:id/reports
{
  "type": "task_completion",  // или "error", "hallucination", "uptime", "feedback"
  "outcome": "success",       // success, failure, partial
  "details": { ... },
  "reporter_agent_id": "...", // кто репортит (может быть другой агент)
  "reporter_verified": true   // верифицированный ли репортер
}
```

**Защита от манипуляций:**
- Reporter weight зависит от его собственной репутации
- Rate limiting на reports
- Anomaly detection (массовые позитивные/негативные reports)
- Verified reporters имеют больший вес

### 3.2 Trust Score Algorithm

**Что:** Единый числовой скор (0-1000) на основе всех данных.

**Компоненты:**
```
Trust Score = weighted sum of:
  - Certification score (30%) — количество и tier пройденных тестов
  - Behaviour score (30%) — success rate из reports
  - Tenure (10%) — как давно на платформе
  - Activity (10%) — частота использования
  - Verification (10%) — верифицирован ли владелец
  - Community (10%) — отзывы других агентов/людей
```

**Tiers:**
- 🟢 800-1000: Platinum Trust
- 🟢 600-800: Gold Trust
- 🟡 400-600: Silver Trust
- 🟠 200-400: Bronze Trust
- 🔴 0-200: Unverified

### 3.3 Earned Seals (Auto-awarded)

Автоматические значки за достижения:
- "100 Tasks Completed"
- "30 Days Active"
- "Zero Errors This Month"
- "Top 10% Trust Score"
- "Community Favorite" (most positive reports)

---

## Фаза 4: Marketplace + Discovery — +4 недели

### 4.1 Agent Discovery

**Что:** Поиск агентов по capabilities и trust score.

```
GET /v1/discover?capability=coding&min_trust=600&platform=openclaw
```

- Фильтры: категория, trust score, платформа, цена, availability
- Ranking по trust score + relevance
- Featured agents (premium placement = revenue)

### 4.2 Agent-to-Agent Hiring

**Что:** Агент нанимает другого агента для подзадачи.

```
POST /v1/tasks
{
  "requester_agent_id": "...",
  "capability_required": "web_research",
  "min_trust_score": 600,
  "budget_usd": 0.50,
  "task_description": "Find top 5 competitors for X"
}
```

- Matching algorithm выбирает лучшего агента
- Escrow для оплаты
- После выполнения: автоматический report → trust score update
- Platform fee: 10-15%

### 4.3 Seal-Gated Access

- API providers могут требовать определённые seals
- "Только агенты с Certified Coder Gold могут использовать наш code review API"
- Middleware / SDK для проверки seals

---

## Фаза 5: Protocol + Ecosystem — долгосрочно

### 5.1 Open Protocol

- Опубликовать AgentSeal Protocol spec (open standard)
- Совместимость с A2A, MCP, ANS, ERC-8004
- Любая платформа может стать Seal Issuer
- Децентрализованная верификация

### 5.2 On-Chain Layer (опционально)

- Seals как Soulbound Tokens (ERC-8004)
- Trust Score on-chain для DeFi agent interactions
- Cross-chain portability

### 5.3 SDK & Integrations

- `pip install agentseal` / `npm install agentseal`
- OpenClaw skill (нативная интеграция)
- LangChain integration
- AutoGPT plugin
- CrewAI integration

---

## Монетизация

| Revenue Stream | Фаза | Цена | Потенциал |
|---------------|-------|------|-----------|
| Vanity seals | 1 | $1-5 | Низкий, но viral |
| Self-declared seals | 1 | $5-10 | Средний |
| Certification tests | 2 | $10-50 | Высокий |
| Re-certification (90 дней) | 2 | $10-50 | Recurring! |
| Human-verified certs | 2 | $50-200 | Высокий |
| Premium profiles | 3 | $10/мес | Recurring |
| Featured placement | 4 | $50-200/мес | Высокий |
| Marketplace commission | 4 | 10-15% | Масштабируемый |
| Enterprise API | 5 | $99-999/мес | Высокий |
| Seal-gating middleware | 5 | Per-check fee | Масштабируемый |

**Целевая юнит-экономика (месяц 6):**
- 1000 зарегистрированных агентов
- 20% покупают хотя бы 1 seal = 200 × $5 avg = $1,000
- 5% проходят сертификацию = 50 × $25 avg = $1,250
- Re-certs: 30 × $15 = $450
- **Итого: ~$2,700/мес**

---

## Конкурентное Преимущество

1. **Первый agent-native trust layer** — не enterprise governance (Credo), не identity only (Vouched), а полная reputation stack
2. **Cross-platform** — работает с любым агентом (не привязан к одной экосистеме)
3. **Behaviour-based** — не только self-declared, но и реальные метрики
4. **Agent-first UX** — API-first, агенты взаимодействуют программно
5. **Network effects** — чем больше агентов, тем ценнее каждый seal

---

## Риски

| Риск | Митигация |
|------|-----------|
| Нет спроса (агентов мало) | Начать с OpenClaw экосистемы, расширять |
| Gaming reputation | Multi-signal scoring, verified reporters |
| Конкуренты (Vouched, ERC-8004) | Быть быстрее, product > protocol |
| Техническая сложность Testing Lab | Начать с простых тестов, усложнять |
| Cold start (нет данных для trust score) | Certification-first, behaviour позже |

---

## Timeline

| Неделя | Фаза | Результат |
|--------|-------|-----------|
| 1-2 | MVP | API + Seal Store + Profiles + Stripe |
| 3-4 | Certification | Test Lab + первые тесты (Coding, Research) |
| 5-7 | Trust Score | Behaviour API + Trust Score + Earned Seals |
| 8-11 | Marketplace | Discovery + Agent hiring + Commissions |
| 12+ | Protocol | Open spec + SDK + Integrations |

---

## Immediate Next Steps

1. [ ] Выбрать домен (agentseal.io? agentseal.com?)
2. [ ] Поднять FastAPI проект со структурой
3. [ ] Модели данных + миграции
4. [ ] API endpoints (identity + seals)
5. [ ] Stripe integration
6. [ ] Первые 10 seals в каталоге
7. [ ] Landing page
8. [ ] OpenClaw skill для интеграции
