# Leafleter

<p align="center">
  <img src="leafleter.png" alt="Logo" width="300" />
</p>

**Multi-tenant SaaS platform for AI-powered market intelligence, social listening, competitor analysis, trend discovery, and automated reporting.**

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Development](#development)
7. [Deployment](#deployment)
8. [API Documentation](#api-documentation)
9. [Authentication & Security](#authentication--security)
10. [AI Provider Support](#ai-provider-support)
11. [Search & Web Intelligence](#search--web-intelligence)
12. [Analysis Engine](#analysis-engine)
13. [Reporting](#reporting)
14. [Scheduling & Automation](#scheduling--automation)
15. [Notifications](#notifications)
16. [Alert Rules](#alert-rules)
17. [Competitor Intelligence](#competitor-intelligence)
18. [Team Collaboration](#team-collaboration)
19. [White Label](#white-label)
20. [Testing](#testing)
21. [Monitoring & Observability](#monitoring--observability)
22. [License](#license)

---

## Overview

Leafleter enables organizations to monitor markets, competitors, brands, and trends by combining multiple AI providers, social connectors, web search, crawling, and scheduled analysis into a single collaborative workspace.

The platform is designed as a **multi-tenant SaaS** with strict organization isolation, role-based access control (RBAC), audit logging, and a provider-agnostic AI abstraction layer.

---

## Key Features

### Multi-Tenant SaaS Foundation

- Organization-based tenant isolation
- User management and role-based access control
- API key management with scoped permissions
- Audit logging and soft-delete support
- White-label branding for agencies

### AI Provider Management

- Support for 8+ AI providers
- Provider connection testing
- Default provider and fallback chain
- Per-request cost tracking
- Model selection and pricing configuration

### Topic Workspaces

- Create research topics
- Attach multiple sources (search, URL, sitemap, social)
- Run AI-powered analysis
- Chat with collected data
- Save conversation history

### Analysis Engine

- Sentiment analysis
- Trend analysis
- Competitor/SWOT analysis
- Audience insights
- Pain-point detection
- Opportunity detection
- Brand reputation scoring

### Search & Web Intelligence

- Multi-engine web search (SerpAPI, Bing, Tavily, Google CSE)
- Web page crawling with content extraction
- Sitemap parsing
- Competitor website monitoring

### Reports

- Generate reports in Markdown, PDF, DOCX, PPTX
- Report templates
- Report approval workflow
- Report comments for collaboration
- Downloadable files via static storage

### Scheduling & Automation

- Cron-based schedule builder
- Recurring analysis jobs
- Report generation jobs
- Brand monitoring jobs
- Competitor snapshot jobs
- Job execution monitoring

### Notifications

- Email (SMTP)
- Slack webhooks
- Microsoft Teams webhooks
- Discord webhooks
- WhatsApp / Messenger (extensible stubs)

### Alert Rules

- Threshold-based alerting
- Metric conditions (>, <, >=, <=, =)
- Cooldown periods
- Multi-channel notifications
- Alert history

### Competitor Intelligence

- Competitor watchlists
- Website snapshots
- Change tracking foundation
- Social growth tracking hooks

### Advanced AI Features

- AI Debate Engine (multi-provider consensus)
- Content Generator (LinkedIn, X, Instagram, blog)
- Campaign Analyzer
- Lead Discovery

### Real-Time Dashboard

- Live organization stat cards (topics, competitors, sources, alerts, intelligence items, facts)
- 30-day AI spend and token usage analytics
- Daily cost trend line chart and provider cost bar chart
- WebSocket-powered live updates with connection indicator

### Team Collaboration

- User invitations
- Report comments
- Shared dashboards
- Report approvals

---

## Technology Stack

### Frontend

- React 18
- TypeScript
- Vite
- TailwindCSS
- Shadcn/UI
- TanStack Query
- React Router
- Zustand
- Recharts

### Backend

- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- APScheduler
- SQLite (development)
- PostgreSQL (production)
- Alembic migrations
- httpx
- python-jose
- passlib/bcrypt
- Jinja2
- python-docx / python-pptx / WeasyPrint / markdown

### Infrastructure

- Docker
- Docker Compose
- Kubernetes
- Prometheus metrics
- Structured logging with structlog

---

## Project Structure

```
Marketo/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers
│   │   ├── core/            # Config, security, logging, deps
│   │   ├── crud/            # Repository layer
│   │   ├── db/              # SQLAlchemy base, session, init
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic DTOs
│   │   ├── services/        # Business logic
│   │   ├── providers/       # AI provider adapters
│   │   ├── connectors/      # Social connectors
│   │   ├── search/          # Search engines + crawler
│   │   ├── analysis/        # Analysis engines
│   │   ├── reporting/       # Report generators
│   │   ├── scheduler/       # APScheduler jobs
│   │   ├── notifications/   # Notification channels
│   │   ├── plugins/         # Plugin system
│   │   ├── utils/           # Crypto, slug, storage
│   │   └── tests/           # Pytest tests
│   ├── alembic/             # Database migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/      # UI + layout components
│   │   ├── pages/           # Route pages
│   │   ├── services/        # API clients
│   │   ├── stores/          # Zustand stores
│   │   ├── hooks/           # Custom hooks
│   │   ├── types/           # TypeScript types
│   │   └── lib/             # Utilities
│   └── package.json
├── infra/
│   ├── docker/              # Dockerfiles + nginx
│   └── k8s/                 # Kubernetes manifests
├── docs/
│   ├── phase1/              # Architecture design
│   ├── phase2/              # Roadmap
│   └── phase3/              # Structure
├── README.md
├── setup.md
├── architecture.md
├── docker-compose.yml
├── docker-compose.prod.yml
└── Makefile
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) Docker and Docker Compose

### 1. Clone and Configure

```bash
cd Marketo
cp backend/.env.example backend/.env
# Edit backend/.env with your secrets
```

### 2. Start Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8085`.

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5240`.

### Windows One-Click Start

Double-click `start-dev.bat` in the project root to launch both the backend and frontend in separate windows.

### 4. Access API Docs

- Swagger UI: `http://localhost:8085/docs`
- ReDoc: `http://localhost:8085/redoc`

---

## Development

### Backend Commands

```bash
cd backend

# Run server
uvicorn app.main:app --reload

# Run tests
pytest

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"
```

### Frontend Commands

```bash
cd frontend

# Dev server
npm run dev

# Production build
npm run build

# Preview build
npm run preview

# Run tests
npm test
```

### Using Make

```bash
make backend    # Start backend
make frontend   # Start frontend
make test       # Run all tests
make docker     # Start with Docker Compose
```

---

## Deployment

### Docker Compose (Development)

```bash
docker compose up --build
```

This starts:

- Backend API on port 8085
- Frontend on port 5240
- Scheduler service
- Redis
- MinIO object storage

### Docker Compose (Production)

```bash
cp backend/.env.example .env
# Fill in production values
docker compose -f docker-compose.prod.yml up --build -d
```

Production stack includes:

- Backend API (replicas: 2)
- Scheduler service
- Frontend (replicas: 2)
- PostgreSQL
- Redis

### Kubernetes

```bash
cd infra/k8s
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f backend.yaml
kubectl apply -f scheduler.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml
```

Update `infra/k8s/secret.yaml` with production secrets before applying.

---

## API Documentation

All API endpoints are versioned under `/api/v1/`.

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/api-keys`

### Organizations & Users

- `GET /api/v1/organizations/me`
- `PUT /api/v1/organizations/me`
- `PUT /api/v1/organizations/me/branding`
- `GET/POST /api/v1/users`
- `GET/PUT/DELETE /api/v1/users/{id}`
- `GET/POST /api/v1/roles`
- `GET/POST /api/v1/api-keys`

### Providers

- `GET /api/v1/providers`
- `POST /api/v1/providers`
- `GET /api/v1/providers/types`
- `POST /api/v1/providers/{id}/test`
- `POST /api/v1/providers/{id}/chat`

### Search

- `POST /api/v1/search`
- `POST /api/v1/search/crawl`
- `POST /api/v1/search/sitemap`

### Topics

- `GET/POST /api/v1/topics`
- `GET/PUT/DELETE /api/v1/topics/{id}`
- `POST /api/v1/topics/{id}/sources`
- `POST /api/v1/topics/{id}/analyze`
- `GET /api/v1/topics/{id}/runs`

### Chat

- `GET/POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{id}`
- `POST /api/v1/chat/sessions/{id}/messages`

### Reports

- `GET/POST /api/v1/reports`
- `GET/PUT /api/v1/reports/{id}`
- `GET/POST /api/v1/reports/{id}/comments`

### Schedules & Jobs

- `GET/POST /api/v1/schedules`
- `GET/PUT/DELETE /api/v1/schedules/{id}`
- `GET /api/v1/jobs`

### Notifications

- `GET/POST /api/v1/notifications`
- `PUT /api/v1/notifications/{id}`

### Alerts

- `GET/POST /api/v1/alert-rules`
- `GET/PUT/DELETE /api/v1/alert-rules/{id}`
- `GET /api/v1/alerts`

### Competitors

- `GET/POST /api/v1/competitors`
- `GET/PUT/DELETE /api/v1/competitors/{id}`
- `POST /api/v1/competitors/{id}/snapshots`

### Advanced

- `POST /api/v1/debate`
- `POST /api/v1/content/generate`
- `POST /api/v1/campaigns/analyze`
- `POST /api/v1/leads/discover`

### Dashboard

- `GET /api/v1/dashboard/snapshot` — current stats and 30-day cost analytics
- `WS /api/v1/dashboard/ws` — live dashboard snapshot stream

---

## Authentication & Security

- JWT access tokens (15-minute expiry)
- Rotating refresh tokens
- bcrypt password hashing
- API keys with HMAC hashing
- Role-based access control (RBAC)
- Organization isolation at repository layer
- CORS protection
- Input validation via Pydantic v2
- SQL injection prevention via SQLAlchemy ORM
- Encrypted provider credentials at rest (Fernet)
- Audit logging hooks

---

## AI Provider Support

Supported providers:

| Provider         | Notes                                       |
| ---------------- | ------------------------------------------- |
| OpenAI           | Chat completions, embeddings, model listing |
| Azure OpenAI     | Config validation + model list              |
| Anthropic Claude | Config validation + model list              |
| Google Gemini    | Config validation + model list              |
| OpenRouter       | Config validation + model list              |
| AWS Bedrock      | Config validation + model list              |
| Moonshot Kimi    | Config validation + model list              |
| Alibaba Qwen     | Config validation + model list              |

Stubs follow the same `BaseProvider` interface and can be fully implemented by adding the provider SDK call in the respective adapter file.

---

## Search & Web Intelligence

Search engines:

- SerpAPI (full httpx implementation)
- Bing Search
- Tavily
- Google Custom Search Engine

Web intelligence:

- URL crawling with httpx + BeautifulSoup
- Sitemap XML parsing
- Content extraction (title, text, links)

---

## Analysis Engine

Available analysis types:

- `sentiment`
- `trends`
- `swot`
- `audience`
- `reputation`
- `pain_points`
- `opportunities`

Each engine uses the organization's configured AI provider and records cost to the ledger.

---

## Reporting

Supported formats:

- Markdown
- PDF (via WeasyPrint)
- DOCX
- PPTX

Reports aggregate analysis results and topic sources into branded documents.

---

## Scheduling & Automation

Schedule types:

- `re_analysis` — re-run topic analysis
- `report_generation` — generate scheduled reports
- `brand_monitor` — fetch new mentions
- `competitor_snapshot` — capture competitor changes

Schedules use cron expressions and are synchronized with APScheduler.

---

## Notifications

Channels:

- Email via SMTP
- Slack incoming webhooks
- Microsoft Teams incoming webhooks
- Discord incoming webhooks
- WhatsApp / Messenger (extensible stubs)

Each notification is persisted with delivery status.

---

## Alert Rules

Alert rules evaluate analysis results and trigger notifications when conditions are met:

- `metric`: analysis result type (e.g., sentiment, reputation)
- `condition`: gt, lt, gte, lte, eq
- `threshold`: numeric value
- `cooldown_minutes`: minimum time between triggers
- `notification_channels`: comma-separated channel list

---

## Competitor Intelligence

Track competitors by:

- Website URL
- Industry
- Social handles
- Watch configuration

Capture scheduled snapshots and compare content changes over time.

---

## Team Collaboration

- Invite team members
- Assign roles (Owner, Admin, Analyst, Viewer, custom)
- Comment on reports
- Approve reports
- Shared dashboards

---

## White Label

Organizations can configure:

- Primary brand color
- Logo URL
- Favicon URL
- Custom domain

These settings can be applied to the frontend for agency/customer branding.

---

## Testing

### Backend Tests

```bash
cd backend
pytest
```

Current tests cover:

- User registration
- User login
- Invalid credential handling

Add more tests in `backend/app/tests/`.

### Frontend Tests

```bash
cd frontend
npm test
```

---

## Monitoring & Observability

- `/health` — liveness probe
- `/ready` — readiness probe
- `/metrics` — Prometheus metrics
- Structured JSON logging via structlog
- Provider registration logs
- AI request cost ledger
- Job execution logs
- Audit log model

---

## License

MIT License — see the project license for details.

---

## Support & Contribution

For questions, issues, or contributions, refer to the project repository and follow the existing code style and architecture patterns documented in `architecture.md` and `setup.md`.
