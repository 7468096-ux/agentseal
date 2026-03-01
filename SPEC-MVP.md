# AgentSeal MVP — Детальная Спецификация

> Этот документ — исчерпывающее ТЗ для разработки MVP.
> Написан так, чтобы любой AI-агент мог реализовать без дополнительных уточнений.

---

## 0. Prompt Library Analysis

### 🔍 Verification Protocol

**Какие предположения мы делаем?**
1. AI агентам (их владельцам) нужна репутация — ПРЕДПОЛОЖЕНИЕ. Пока нет валидации рынком.
2. Владельцы агентов готовы платить $1-50 за значки — ПРЕДПОЛОЖЕНИЕ. Нет данных о willingness to pay.
3. 1000 агентов за 6 месяцев — ОПТИМИСТИЧНО. Нет каналов привлечения.
4. Агенты могут программно взаимодействовать с API — ВЕРНО для OpenClaw/LangChain, не для всех.
5. Cross-platform reputation будет востребована — ПРЕДПОЛОЖЕНИЕ. Большинство агентов живут внутри одной экосистемы.

**Какие данные подтверждают?**
- Vouched.id получил $17M Series A на agent identity — инвесторы верят в рынок
- ERC-8004 (MetaMask + Ethereum Foundation) — крупные игроки работают над стандартом
- Google A2A + MCP — инфраструктура agent-to-agent взаимодействия растёт
- Skyfire + Stripe делают agent payments — агенты начинают "покупать"

**Что может пойти не так?**
- Нет спроса: владельцы агентов не видят ценности в значках
- Vouched.id или Google выкатят свою систему бейджей
- Технически сложно: агенты из разных экосистем не смогут интегрироваться
- Холодный старт: пустая платформа без агентов никому не интересна

**Worst case scenario:**
Потратим 2-4 недели на MVP, никто не зарегистрируется. Потери: время + ~$10 на хостинг. Приемлемый риск.

### 🧱 First Principles

**Базовые компоненты проблемы:**
1. **Идентификация** — кто этот агент? → Agent Registry
2. **Заявление** — что этот агент умеет? → Seals (значки)
3. **Доказательство** — правда ли это? → Certification (фаза 2)
4. **Отзывы** — как он себя ведёт? → Behaviour tracking (фаза 3)
5. **Обнаружение** — как найти нужного агента? → Discovery (фаза 4)

**Что точно известно:**
- API для агентов — это REST + JSON, без вариантов
- Нужна аутентификация (API key на старте, OAuth позже)
- Данные хранятся в PostgreSQL (проверено на SmartHelp)
- Stripe работает для онлайн-платежей
- FastAPI — знакомый стек, быстрая разработка

**Фундаментальные ограничения:**
- MVP должен работать на одном VPS ($5-10/мес)
- Один разработчик (Coder агент) + один архитектор (Alice)
- Бюджет на инфраструктуру: ~$20/мес максимум
- Время до первого прототипа: 2 недели

**Решение снизу вверх:**
MVP = REST API + PostgreSQL + простая веб-страница профиля. Без фронтенд-фреймворков, без микросервисов, без блокчейна. Максимально просто.

### 😈 Devil's Advocate

**Почему это НЕ сработает?**
1. Vanity badges для агентов — это как NFT для ботов. Кто реально будет покупать?
2. Без certification (фаза 2) значки ничего не значат — просто картинки
3. Холодный старт: зачем регистрировать агента на платформе где нет других агентов?
4. OpenClaw community маленькое — не хватит для критической массы

**Контраргументы и решения:**
1. Фокус не на vanity, а на self-declared → certified путь. Vanity — это viral loop, не основной продукт.
2. Первые 2 недели — identity + self-declared. Certification через 2 недели. Быстрая итерация.
3. Cold start решаем: (a) сами регистрируем наших агентов, (b) партнёрство с OpenClaw для нативной интеграции, (c) бесплатная регистрация + 1 бесплатный seal
4. Целевая аудитория шире OpenClaw: LangChain, AutoGPT, CrewAI, custom агенты

**Скрытые расходы/риски:**
- Поддержка API: если кто-то начнёт использовать, нужно поддерживать backwards compatibility
- Модерация: если открыть регистрацию, будет спам/абьюз
- Security: API keys, payment данные — нужна базовая безопасность

**Что если рынок изменится?**
- Agent экосистема может консолидироваться вокруг одного стандарта (MCP?) → адаптируемся
- Большие игроки (Google, Microsoft) могут сделать свою систему → наш шанс быть open/cross-platform альтернативой

### 💡 Think Out of Box

**Смежные возможности:**
- **Agent Directory** — просто каталог агентов БЕЗ значков уже имеет ценность (SEO, discovery)
- **Agent Analytics** — сколько раз проверяли профиль агента, откуда трафик
- **Embed Widget** — владельцы сайтов вставляют "Verified by AgentSeal" бейдж
- **API для проверки** — другие платформы проверяют seal агента перед взаимодействием (как SSL check)

**Что если перевернуть проблему?**
Вместо "агенты покупают значки" → "платформы покупают верификацию своих агентов". B2B вместо B2C. Но это фаза 2+.

**Что мы уже умеем?**
- FastAPI + PostgreSQL (SmartHelp)
- VPS management (AWS)
- AI agents (OpenClaw) — мы сами пользователи своего продукта!
- Crypto payments (Bybit опыт)

---

## 1. Архитектура MVP

### 1.1 Компоненты

```
┌─────────────────────────────────────────┐
│            AgentSeal MVP                 │
│                                          │
│  ┌──────────────┐   ┌────────────────┐  │
│  │  FastAPI App  │   │  PostgreSQL    │  │
│  │              │───│  Database      │  │
│  │  /v1/agents  │   │               │  │
│  │  /v1/seals   │   │  agents       │  │
│  │  /v1/pay     │   │  seals        │  │
│  │              │   │  agent_seals  │  │
│  │  /profile/*  │   │  payments     │  │
│  │  (HTML)      │   │  api_keys     │  │
│  └──────┬───────┘   └────────────────┘  │
│         │                                │
│  ┌──────┴───────┐   ┌────────────────┐  │
│  │  Stripe SDK  │   │  Jinja2        │  │
│  │  (payments)  │   │  (templates)   │  │
│  └──────────────┘   └────────────────┘  │
└─────────────────────────────────────────┘
```

### 1.2 Стек

| Компонент | Технология | Почему |
|-----------|-----------|--------|
| Backend | FastAPI (Python 3.11+) | Знакомый, быстрый, async |
| Database | PostgreSQL 15+ | JSONB для metadata, надёжный |
| ORM | SQLAlchemy 2.0 + Alembic | Миграции, type safety |
| Templates | Jinja2 (встроен в FastAPI) | Для профилей, без SPA |
| Payments | Stripe Checkout | Проверенный, быстрая интеграция |
| Auth | API Key (header: `X-API-Key`) | Просто, понятно агентам |
| Hosting | VPS (Hetzner CX22 или AWS) | $4-5/мес |
| Reverse Proxy | Caddy | Auto-TLS, простой конфиг |

### 1.3 Нефункциональные требования

- **Latency:** < 200ms на любой endpoint
- **Availability:** 99% (одна VPS, без HA на старте)
- **Security:** HTTPS only, API keys hashed (bcrypt), rate limiting (60 req/min)
- **Data:** Бэкапы PostgreSQL ежедневно (pg_dump → S3 или local)

---

## 2. Модель данных

### 2.1 Таблица `agents`

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,  -- для URL: agentseal.io/@slug
    description TEXT,
    platform VARCHAR(32) NOT NULL DEFAULT 'custom',
        -- enum: 'openclaw', 'langchain', 'autogpt', 'crewai', 'custom'
    owner_email VARCHAR(255),  -- nullable, для верификации
    owner_verified BOOLEAN NOT NULL DEFAULT FALSE,
    avatar_url VARCHAR(512),
    website_url VARCHAR(512),
    metadata JSONB NOT NULL DEFAULT '{}',
        -- свободные поля: version, capabilities, github, etc.
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_slug ON agents(slug);
CREATE INDEX idx_agents_platform ON agents(platform);
CREATE INDEX idx_agents_created ON agents(created_at);
```

**Валидация:**
- `name`: 2-64 символа, alphanumeric + пробелы + дефисы
- `slug`: 2-64 символа, lowercase, alphanumeric + дефисы, уникальный
- `platform`: один из enum значений
- `owner_email`: валидный email или NULL
- `metadata`: максимум 10KB JSON

### 2.2 Таблица `api_keys`

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    key_hash VARCHAR(128) NOT NULL,  -- bcrypt hash
    key_prefix VARCHAR(8) NOT NULL,  -- первые 8 символов для идентификации: "as_live_"
    name VARCHAR(64) NOT NULL DEFAULT 'default',
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- nullable = never expires
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_agent ON api_keys(agent_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

**Формат API Key:** `as_live_{32 random hex chars}` (пример: `as_live_a1b2c3d4e5f6...`)
**Хранение:** только bcrypt hash. Оригинальный ключ показывается ОДИН раз при создании.

### 2.3 Таблица `seals`

```sql
CREATE TABLE seals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(20) NOT NULL,
        -- enum: 'vanity', 'self_declared', 'certified', 'earned'
    tier VARCHAR(10),
        -- enum: NULL, 'bronze', 'silver', 'gold', 'platinum'
    price_cents INTEGER NOT NULL DEFAULT 0,  -- цена в центах USD, 0 = бесплатный
    icon_emoji VARCHAR(10),  -- emoji для отображения: 🏆, ⭐, 🛡️
    color VARCHAR(7),  -- hex color: #FFD700
    max_supply INTEGER,  -- NULL = unlimited
    issued_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requirements JSONB,  -- для certified/earned: критерии получения
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seals_category ON seals(category);
CREATE INDEX idx_seals_slug ON seals(slug);
```

### 2.4 Таблица `agent_seals`

```sql
CREATE TABLE agent_seals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    seal_id UUID NOT NULL REFERENCES seals(id) ON DELETE RESTRICT,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL = never
    proof JSONB,  -- для certified: результаты теста; для earned: метрики
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_reason VARCHAR(255),
    payment_id UUID REFERENCES payments(id),
    
    UNIQUE(agent_id, seal_id)  -- один seal одного типа на агента
);

CREATE INDEX idx_agent_seals_agent ON agent_seals(agent_id);
CREATE INDEX idx_agent_seals_seal ON agent_seals(seal_id);
```

### 2.5 Таблица `payments`

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- enum: 'pending', 'completed', 'failed', 'refunded'
    provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
    provider_payment_id VARCHAR(255),  -- Stripe payment_intent ID
    provider_checkout_url VARCHAR(512),  -- Stripe checkout session URL
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_payments_agent ON payments(agent_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_id ON payments(provider_payment_id);
```

---

## 3. API Endpoints

### 3.1 Аутентификация

Все мутирующие endpoints требуют API key в заголовке:
```
X-API-Key: as_live_a1b2c3d4...
```

Публичные endpoints (GET) доступны без аутентификации.

Middleware проверяет:
1. Наличие заголовка `X-API-Key`
2. Поиск по `key_prefix` (первые 8 символов)
3. bcrypt.verify полного ключа
4. `is_active = true` и `expires_at` не истёк
5. Обновление `last_used_at`
6. Привязка `agent_id` к request scope

### 3.2 Agents API

#### `POST /v1/agents` — Регистрация агента
**Auth:** Не требуется (создаёт нового агента + API key)

**Request:**
```json
{
    "name": "Alice",
    "slug": "alice-v3",           // optional, auto-generated from name if missing
    "description": "AI assistant living on Mac Mini M4",
    "platform": "openclaw",       // optional, default "custom"
    "owner_email": "user@example.com",  // optional
    "avatar_url": "https://...",  // optional
    "website_url": "https://...", // optional
    "metadata": {                 // optional, freeform
        "version": "3.0",
        "capabilities": ["coding", "research", "trading"]
    }
}
```

**Response (201):**
```json
{
    "agent": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Alice",
        "slug": "alice-v3",
        "description": "AI assistant living on Mac Mini M4",
        "platform": "openclaw",
        "owner_verified": false,
        "avatar_url": null,
        "website_url": null,
        "metadata": {"version": "3.0", "capabilities": ["coding", "research", "trading"]},
        "seals": [],
        "created_at": "2026-02-26T12:00:00Z",
        "profile_url": "https://agentseal.io/@alice-v3"
    },
    "api_key": "as_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "warning": "Save this API key — it will not be shown again."
}
```

**Ошибки:**
- 400: Invalid input (name too short, slug taken, invalid platform)
- 429: Rate limit exceeded (max 10 registrations per IP per hour)

---

#### `GET /v1/agents/:id` — Профиль агента
**Auth:** Не требуется

**Response (200):**
```json
{
    "id": "550e8400-...",
    "name": "Alice",
    "slug": "alice-v3",
    "description": "AI assistant living on Mac Mini M4",
    "platform": "openclaw",
    "owner_verified": false,
    "avatar_url": null,
    "website_url": null,
    "metadata": {"version": "3.0"},
    "seals": [
        {
            "id": "...",
            "seal_name": "Early Adopter",
            "seal_slug": "early-adopter",
            "category": "vanity",
            "tier": null,
            "icon_emoji": "🌟",
            "color": "#FFD700",
            "issued_at": "2026-02-26T12:05:00Z",
            "expires_at": null
        }
    ],
    "seal_count": 1,
    "created_at": "2026-02-26T12:00:00Z",
    "profile_url": "https://agentseal.io/@alice-v3"
}
```

**Также доступно по slug:** `GET /v1/agents/by-slug/:slug`

---

#### `PATCH /v1/agents/:id` — Обновление профиля
**Auth:** Требуется (только свой профиль)

**Request:** любое подмножество полей из POST
**Response:** обновлённый профиль агента

**Ошибки:**
- 401: Missing/invalid API key
- 403: API key не принадлежит этому агенту
- 404: Agent not found

---

#### `GET /v1/agents/:id/card` — A2A-совместимый Agent Card
**Auth:** Не требуется

**Response (200):**
```json
{
    "name": "Alice",
    "description": "AI assistant living on Mac Mini M4",
    "url": "https://agentseal.io/@alice-v3",
    "provider": {
        "organization": "AgentSeal",
        "url": "https://agentseal.io"
    },
    "version": "1.0",
    "capabilities": {
        "seals": ["early-adopter"],
        "trust_score": null
    },
    "authentication": {
        "schemes": ["apiKey"]
    }
}
```

---

### 3.3 Seals API

#### `GET /v1/seals` — Каталог значков
**Auth:** Не требуется

**Query params:**
- `category` — фильтр: vanity, self_declared, certified, earned
- `limit` — default 50, max 100
- `offset` — для пагинации

**Response (200):**
```json
{
    "seals": [
        {
            "id": "...",
            "name": "Early Adopter",
            "slug": "early-adopter",
            "description": "One of the first agents on AgentSeal",
            "category": "vanity",
            "tier": null,
            "price_cents": 100,
            "price_display": "$1.00",
            "icon_emoji": "🌟",
            "color": "#FFD700",
            "max_supply": 1000,
            "issued_count": 42,
            "available": true
        }
    ],
    "total": 15,
    "limit": 50,
    "offset": 0
}
```

---

#### `GET /v1/seals/:id` — Детали значка
**Auth:** Не требуется

**Response:** один объект seal + список последних 10 агентов с этим seal

---

#### `POST /v1/agents/:id/seals` — Получить/купить значок
**Auth:** Требуется

**Request:**
```json
{
    "seal_slug": "early-adopter"
}
```

**Логика:**
1. Проверить: агент не имеет этот seal
2. Проверить: seal is_active и supply не исчерпан
3. Если `price_cents == 0`: выдать сразу
4. Если `price_cents > 0`: создать Stripe Checkout Session, вернуть URL

**Response (бесплатный seal, 201):**
```json
{
    "agent_seal": {
        "id": "...",
        "seal": { ... },
        "issued_at": "2026-02-26T12:05:00Z",
        "expires_at": null
    }
}
```

**Response (платный seal, 202):**
```json
{
    "payment_required": true,
    "checkout_url": "https://checkout.stripe.com/c/pay/...",
    "payment_id": "...",
    "expires_in_seconds": 1800
}
```

**Ошибки:**
- 400: Already has this seal
- 404: Seal not found
- 410: Seal supply exhausted

---

#### `GET /v1/agents/:id/seals` — Значки агента
**Auth:** Не требуется

**Response (200):**
```json
{
    "seals": [
        {
            "seal_name": "Early Adopter",
            "seal_slug": "early-adopter",
            "category": "vanity",
            "icon_emoji": "🌟",
            "issued_at": "2026-02-26T12:05:00Z",
            "expires_at": null,
            "revoked": false
        }
    ],
    "count": 1
}
```

---

#### `DELETE /v1/agents/:id/seals/:seal_id` — Отказаться от значка
**Auth:** Требуется
**Response:** 204 No Content (seal помечается revoked)

---

### 3.4 Payment Webhook

#### `POST /v1/webhooks/stripe` — Stripe webhook
**Auth:** Stripe signature verification

**Обрабатываемые события:**
- `checkout.session.completed` → обновить payment status, выдать seal
- `payment_intent.payment_failed` → обновить payment status

---

### 3.5 Public Profiles (HTML)

#### `GET /@:slug` — Публичный профиль агента
**Response:** HTML-страница (Jinja2 template)

Содержимое:
- Имя, описание, платформа
- Аватар (или placeholder)
- Список значков с иконками
- Дата регистрации
- Ссылка на JSON API (`/v1/agents/:id`)

#### `GET /directory` — Каталог агентов
**Response:** HTML-страница со списком агентов, отсортированных по количеству seal'ов

#### `GET /` — Landing page
**Response:** Статическая HTML-страница
- Что такое AgentSeal
- Как работает
- Каталог значков
- Кнопка "Register your agent"
- API docs ссылка

---

## 4. Начальный набор Seal'ов (seed data)

### 4.1 Vanity ($1-5)

| Slug | Name | Emoji | Color | Price | Max Supply | Description |
|------|------|-------|-------|-------|------------|-------------|
| `early-adopter` | Early Adopter | 🌟 | #FFD700 | $1.00 | 1000 | One of the first 1000 agents on AgentSeal |
| `night-owl` | Night Owl | 🦉 | #4A0080 | $2.00 | ∞ | For agents that never sleep |
| `pioneer` | Pioneer | 🚀 | #FF4500 | $3.00 | 500 | Among the first 500 agents registered |
| `collector` | Collector | 🏅 | #C0C0C0 | $2.00 | ∞ | Has 5+ seals |
| `seal-enthusiast` | Seal Enthusiast | 🦭 | #87CEEB | $1.00 | ∞ | Loves seals (both kinds) |

### 4.2 Self-Declared ($5-10)

| Slug | Name | Emoji | Color | Price | Description |
|------|------|-------|-------|-------|-------------|
| `coder` | Coder | 💻 | #00D4FF | $5.00 | This agent writes code |
| `researcher` | Researcher | 🔍 | #32CD32 | $5.00 | This agent does research and analysis |
| `trader` | Trader | 📈 | #FFD700 | $5.00 | This agent trades financial instruments |
| `assistant` | Personal Assistant | 🤖 | #9370DB | $5.00 | This agent is a general-purpose assistant |
| `writer` | Writer | ✍️ | #FF6347 | $5.00 | This agent creates content |
| `analyst` | Data Analyst | 📊 | #4169E1 | $5.00 | This agent analyzes data |
| `devops` | DevOps | ⚙️ | #FF8C00 | $7.00 | This agent manages infrastructure |
| `security` | Security Expert | 🛡️ | #DC143C | $10.00 | This agent handles security tasks |
| `polyglot` | Polyglot | 🌍 | #2E8B57 | $5.00 | This agent works in multiple languages |
| `autonomous` | Fully Autonomous | 🧠 | #8B008B | $10.00 | This agent operates without human supervision |

### 4.3 Free (при регистрации)

| Slug | Name | Emoji | Color | Description |
|------|------|-------|-------|-------------|
| `registered` | Registered Agent | ✅ | #00AA00 | Successfully registered on AgentSeal |

---

## 5. Структура проекта

```
projects/agent-reputation/
├── README.md
├── PLAN.md
├── SPEC-MVP.md          ← этот файл
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
│   │   ├── agent.py     ← Pydantic request/response schemas
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
├── seed.py              ← Скрипт заполнения начальных seal'ов
├── requirements.txt
├── Dockerfile
├── docker-compose.yml   ← app + postgres
├── .env.example
├── Caddyfile            ← Reverse proxy + auto-TLS
└── deploy.sh            ← Скрипт деплоя на VPS
```

---

## 6. Конфигурация (Environment Variables)

```env
# Database
DATABASE_URL=postgresql+asyncpg://agentseal:password@localhost:5432/agentseal

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=https://agentseal.io/payment/success
STRIPE_CANCEL_URL=https://agentseal.io/payment/cancel

# App
APP_URL=https://agentseal.io
APP_SECRET_KEY=random-64-char-string  # для CSRF, sessions
ENVIRONMENT=production  # development | production

# Rate Limiting
RATE_LIMIT_REGISTER=10/hour  # per IP
RATE_LIMIT_API=60/minute     # per API key

# Optional
SENTRY_DSN=                   # error tracking
```

---

## 7. Деплой

### 7.1 Инфраструктура

- **VPS:** Hetzner CX22 (2 vCPU, 4GB RAM, 40GB SSD) — €4.35/мес
- **Domain:** agentseal.io (нужно купить)
- **DNS:** Cloudflare (бесплатный)
- **TLS:** Caddy auto-TLS (Let's Encrypt)
- **CI/CD:** Пока ручной деплой через `deploy.sh`

### 7.2 Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: agentseal
      POSTGRES_USER: agentseal
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: unless-stopped

volumes:
  pgdata:
```

### 7.3 deploy.sh

```bash
#!/bin/bash
set -e
HOST="root@<vps-ip>"
ssh $HOST "cd /opt/agentseal && git pull && docker compose build && docker compose up -d"
```

---

## 8. Acceptance Criteria (Definition of Done)

MVP считается готовым когда:

- [ ] `POST /v1/agents` — создаёт агента, возвращает API key
- [ ] `GET /v1/agents/:id` — возвращает профиль с seal'ами
- [ ] `GET /v1/agents/by-slug/:slug` — поиск по slug
- [ ] `PATCH /v1/agents/:id` — обновляет профиль (auth required)
- [ ] `GET /v1/seals` — возвращает каталог seal'ов
- [ ] `POST /v1/agents/:id/seals` — выдаёт бесплатный seal
- [ ] `POST /v1/agents/:id/seals` — создаёт Stripe checkout для платного seal
- [ ] Stripe webhook обрабатывает payment → выдаёт seal
- [ ] `GET /@:slug` — рендерит HTML-профиль
- [ ] `GET /` — landing page
- [ ] `GET /directory` — каталог агентов
- [ ] Rate limiting работает
- [ ] API key auth работает
- [ ] 11 начальных seal'ов в БД (seed data)
- [ ] Registered seal выдаётся автоматически при регистрации
- [ ] Docker compose поднимается одной командой
- [ ] Задеплоено на VPS с HTTPS
- [ ] Базовые тесты проходят (pytest)

---

## 9. Что НЕ входит в MVP

Явный список чтобы избежать scope creep:

- ❌ Certification / Test Lab (фаза 2)
- ❌ Behaviour tracking / Trust Score (фаза 3)
- ❌ Agent discovery search (фаза 4)
- ❌ Agent-to-Agent hiring (фаза 4)
- ❌ Crypto payments (фаза 2)
- ❌ OAuth / JWT auth (API key достаточно)
- ❌ Admin panel
- ❌ Email notifications
- ❌ Seal images/SVG (emoji достаточно)
- ❌ Embed widgets
- ❌ Mobile responsive design (nice to have, not blocker)
- ❌ i18n (English only на старте)
- ❌ Agent deletion (soft-delete через is_active)
- ❌ Multiple API keys per agent (один на старте)
- ❌ Seal transfer between agents
- ❌ Refunds

---

## 10. Open Questions (для решения перед стартом)

1. **Домен:** agentseal.io? agentseal.com? agentseal.dev? Нужно проверить доступность и купить.
2. **Stripe аккаунт:** Есть ли у Александра Stripe аккаунт? Или нужно зарегистрировать?
3. **Хостинг:** Использовать существующий AWS VPS (3.0.92.255) или отдельный Hetzner?
4. **Первый агент:** Зарегистрировать Alice как первого агента на платформе?
5. **Открытая регистрация:** Сразу открыть или invite-only на старте?
