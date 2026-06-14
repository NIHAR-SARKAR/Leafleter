# Architecture Documentation

This document describes the architecture, design patterns, data model, and key flows of Leafleter.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Design Principles](#design-principles)
3. [Component Diagram](#component-diagram)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Database Schema](#database-schema)
7. [Authentication Flow](#authentication-flow)
8. [Multi-Tenancy Model](#multi-tenancy-model)
9. [Provider Abstraction Layer](#provider-abstraction-layer)
10. [Search Framework](#search-framework)
11. [Analysis Pipeline](#analysis-pipeline)
12. [Report Generation Flow](#report-generation-flow)
13. [Scheduler & Job Architecture](#scheduler--job-architecture)
14. [Notification Architecture](#notification-architecture)
15. [Alert Engine](#alert-engine)
16. [Competitor Intelligence](#competitor-intelligence)
17. [Plugin System](#plugin-system)
18. [Security Architecture](#security-architecture)
19. [Scalability & Performance](#scalability--performance)
20. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ React SPA    │  │ Mobile App   │  │ API Clients  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS
┌───────────────────────────▼───────────────────────────────────┐
│                      API Gateway / Ingress                      │
│              (CORS, rate limiting, load balancing)              │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                       FastAPI Backend                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ Auth       │ │ Topics     │ │ Reports    │ │ Scheduler  │  │
│  │ Providers  │ │ Search     │ │ Alerts     │ │ Jobs       │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
└───────────────┬───────────────────────────────┬───────────────┘
                │                               │
    ┌───────────▼──────────┐      ┌─────────────▼────────────┐
    │   SQLAlchemy ORM     │      │     APScheduler          │
    │  (SQLite/PostgreSQL) │      │  (AsyncIO scheduler)     │
    └───────────┬──────────┘      └─────────────┬────────────┘
                │                               │
    ┌───────────▼──────────┐      ┌─────────────▼────────────┐
    │      Database        │      │        Redis             │
    │   (PostgreSQL)       │      │  (Rate limit / cache)    │
    └──────────────────────┘      └──────────────────────────┘
                │
    ┌───────────▼──────────┐
    │   Object Storage     │
    │   (MinIO / S3)       │
    └──────────────────────┘
```

---

## Design Principles

1. **Async-first**: All I/O operations use async/await.
2. **Dependency injection**: FastAPI `Depends` is used for DB sessions and auth.
3. **Repository pattern**: Data access is abstracted through repository classes.
4. **Service layer**: Business logic lives in services, not endpoints.
5. **Multi-tenant by default**: Every query is scoped to `organization_id`.
6. **Provider agnostic**: AI and search engines are pluggable.
7. **Soft deletes**: All models support `deleted_at`.
8. **Auditability**: All models track `created_by_id`, `updated_by_id`, timestamps.
9. **Type safety**: Full typing in Python and TypeScript.
10. **Testability**: Services are decoupled from framework code.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Pages      │ │ Components │ │ Stores     │              │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘              │
│        └──────────────┼──────────────┘                      │
│                       │ Axios + TanStack Query              │
└───────────────────────┼─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                         Backend                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ API Layer (FastAPI routers)                        │    │
│  │ - Auth, Users, Orgs, Roles, Providers, Topics     │    │
│  │ - Reports, Schedules, Alerts, Competitors          │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Service Layer                                       │   │
│  │ - AuthService, TopicService, ReportService          │   │
│  │ - SearchService, AnalysisService, SchedulerService  │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Repository Layer (CRUD abstractions)                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ External Adapters                                   │   │
│  │ - AI providers, Search engines, Crawlers            │   │
│  │ - Social connectors, Notifications                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Directory Organization

```
backend/app/
├── api/v1/           # HTTP routers
├── core/             # Config, security, dependencies, logging
├── crud/             # Repository classes
├── db/               # Base, session, initialization
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response models
├── services/         # Business logic
├── providers/        # AI provider adapters
├── connectors/       # Social platform connectors
├── search/           # Search engines and crawler
├── analysis/         # Analysis engines
├── reporting/        # Report generators
├── scheduler/        # APScheduler integration
├── notifications/    # Notification channels
├── plugins/          # Plugin system
├── utils/            # Helpers
└── tests/            # Tests
```

### Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| API | Route handling, input/output serialization, auth deps |
| Service | Business logic, orchestration, validation |
| Repository | Database access, query building, org scoping |
| Models | Schema definition, relationships |
| Schemas | Validation, DTOs |
| Adapters | External API integration |

---

## Frontend Architecture

### Directory Organization

```
frontend/src/
├── components/       # Reusable UI components
├── pages/            # Route-level pages
├── services/         # API clients
├── stores/           # Zustand state stores
├── hooks/            # Custom React hooks
├── types/            # TypeScript interfaces
├── lib/              # Utilities
└── App.tsx           # Router setup
```

### State Management

- **Zustand**: Authentication and global UI state
- **TanStack Query**: Server state, caching, mutations
- **Local component state**: Form state and UI toggles

### Routing

Protected routes are wrapped in a `Shell` layout. Unauthenticated users are redirected to `/login`.

---

## Database Schema

### Core Entities

```
organizations
├── users
├── roles
├── api_keys
├── providers
├── topics
│   ├── topic_sources
│   ├── topic_runs
│   └── analysis_results
├── chat_sessions
│   └── chat_messages
├── reports
│   ├── report_comments
│   └── report_approvals
├── schedules
├── jobs
├── notification_settings
├── notifications
├── alert_rules
│   └── alerts
├── competitors
│   └── competitor_snapshots
├── cost_ledger
└── audit_logs
```

### Base Model

All models inherit from `Base` + `AuditMixin`:

```python
class AuditMixin:
    id: int PK
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    created_by_id: int | None
    updated_by_id: int | None
```

### Multi-Tenant Queries

All repository queries include:

```python
query = query.where(Model.organization_id == org_id)
query = query.where(Model.deleted_at.is_(None))
```

---

## Authentication Flow

```
User -> POST /auth/register
       AuthService.register()
       -> Create organization
       -> Seed default roles (Owner, Admin, Analyst, Viewer)
       -> Create user with Owner role
       -> Return tokens

User -> POST /auth/login
       AuthService.login()
       -> Verify password
       -> Issue access + refresh tokens
       -> Update last_login_at

User -> Authenticated request
       -> Extract JWT from Authorization header
       -> Decode token
       -> Get current user
       -> Extract organization_id
       -> Pass to service layer
```

### Token Flow

- Access token: short-lived (15 min), contains user_id, org_id, roles
- Refresh token: long-lived (7 days), stored hashed, rotating
- API keys: alternative authentication for integrations

---

## Multi-Tenancy Model

### Isolation Strategy

**Row-level isolation** via `organization_id` foreign key.

### Default Roles

| Role | Permissions |
|------|-------------|
| Owner | Full organization access |
| Admin | Manage users, roles, settings |
| Analyst | Create topics, reports, run analysis |
| Viewer | Read-only access |

### Role-Based Access Control

```python
async def get_current_user_with_permission(permission: str):
    async def wrapper(...):
        user = await get_current_user(...)
        if permission not in user.effective_permissions:
            raise ForbiddenException()
        return user
    return wrapper
```

---

## Provider Abstraction Layer

```
┌─────────────────────────────────────────┐
│         BaseAIProvider                  │
│  + chat_completion()                    │
│  + embed()                              │
│  + list_models()                        │
│  + token_cost()                         │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐
│ OpenAI │  │ AzureAI  │ │ Claude   │ │ Gemini   │
└────────┘  └──────────┘ └──────────┘ └──────────┘
```

### Registry Pattern

```python
provider_registry = AIProviderRegistry()
provider_registry.register("openai", OpenAIProvider)
provider_registry.register("anthropic", AnthropicProvider)
...

provider_class = provider_registry.get(provider_type)
provider = provider_class(config)
response = await provider.chat_completion(messages)
```

### Cost Tracking

Every AI call records:
- Provider and model
- Input/output tokens
- Estimated cost
- Organization ID
- Created timestamp

Stored in `cost_ledger`.

---

## Search Framework

```
┌──────────────────────────────────────────┐
│         BaseSearchEngine                 │
│  + search(query, limit, filters)         │
│  + health_check()                        │
└──────────────────┬───────────────────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│SerpApi │  │ Bing     │  │ Tavily   │  │ GoogleCSE│
└────────┘  └──────────┘  └──────────┘  └──────────┘
```

### Web Crawler

```
URL -> httpx fetch -> BeautifulSoup parse -> Extract title/text/links -> Store content
```

### Search Service

1. Determine search engine from provider settings
2. Execute search
3. Optionally crawl result URLs
4. Store results as `TopicSource`
5. Trigger analysis on demand

---

## Analysis Pipeline

```
Topic Sources -> SearchService.collect_content()
                     │
                     ▼
              Analysis Orchestrator
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
  Sentiment      Trends         SWOT
  Audience       Reputation     Pain Points
       │             │             │
       └─────────────┴─────────────┘
                     │
                     ▼
            Analysis Result Record
                     │
                     ▼
              Cost Ledger Entry
```

### Analysis Types

| Type | Description |
|------|-------------|
| sentiment | Overall sentiment distribution |
| trends | Emerging keywords and topics |
| swot | Strengths, weaknesses, opportunities, threats |
| audience | Audience demographics and interests |
| reputation | Brand reputation score |
| pain_points | Customer pain points |
| opportunities | Market opportunities |

---

## Report Generation Flow

```
Create Report Request
       │
       ▼
Fetch Topic + Analysis Results
       │
       ▼
Select Template
       │
       ▼
Generate Markdown Content
       │
       ▼
Convert to Format (PDF/DOCX/PPTX)
       │
       ▼
Upload to Object Storage
       │
       ▼
Update Report with download_url
       │
       ▼
Notify subscribers
```

---

## Scheduler & Job Architecture

### Components

- `Schedule` model: cron expression, job type, parameters
- `JobExecution` model: tracking
- APScheduler: actual execution
- `scheduler_service`: sync schedules to scheduler

### Job Types

| Type | Action |
|------|--------|
| re_analysis | Re-run topic analysis |
| report_generation | Generate scheduled report |
| brand_monitor | Fetch new brand mentions |
| competitor_snapshot | Capture competitor changes |

### Execution Flow

```
APScheduler tick
    │
    ▼
Load due schedules
    │
    ▼
Create JobExecution (pending)
    │
    ▼
Execute job function
    │
    ▼
Update JobExecution (success/failed)
    │
    ▼
Trigger notifications if configured
```

---

## Notification Architecture

```
Notification Request
       │
       ▼
Channel Router
       │
   ┌───┴───┐
   ▼       ▼
 Email   Slack/Teams/Discord
   │         │
   ▼         ▼
SMTP      Webhook
   │         │
   ▼         ▼
Persist with status
```

### Channels

- Email: aiosmtplib
- Slack: incoming webhook
- Teams: incoming webhook
- Discord: incoming webhook
- WhatsApp/Messenger: extensible stubs

---

## Alert Engine

### Alert Rule Evaluation

```
Analysis Result Created
       │
       ▼
Fetch active alert rules for topic/org
       │
       ▼
Evaluate condition: metric condition threshold
       │
       ▼
Check cooldown period
       │
       ▼
Create Alert + Send Notifications
```

### Conditions

- `gt` (greater than)
- `lt` (less than)
- `gte` (greater than or equal)
- `lte` (less than or equal)
- `eq` (equal)

---

## Competitor Intelligence

```
Competitor Record
       │
       ├── Website URL
       ├── Social handles
       └── Watch config
       │
       ▼
Scheduled Snapshot Job
       │
       ▼
Crawl website -> Extract title, text, links
Fetch social metrics (when connected)
       │
       ▼
Store CompetitorSnapshot
       │
       ▼
Compare with previous snapshot
       │
       ▼
Detect changes -> Trigger alerts
```

---

## Plugin System

The plugin system allows extending analysis engines, notification channels, and report formats.

```
Plugin Base
    │
    ├── AnalysisPlugin
    ├── NotificationPlugin
    └── ReportPlugin

Plugins are discovered from app/plugins/ directory
and registered on startup.
```

---

## Security Architecture

### Authentication
- JWT with HS256
- bcrypt password hashing
- Refresh token rotation
- API key authentication

### Authorization
- RBAC with permissions
- Organization isolation

### Data Protection
- Encrypted provider credentials (Fernet)
- Soft deletes
- Audit logging

### API Security
- Pydantic input validation
- SQL injection prevention via ORM
- CORS configuration
- Rate limiting hooks

### Secrets Management
- Environment variables
- Kubernetes secrets
- Encrypted at rest in DB

---

## Scalability & Performance

### Horizontal Scaling
- Stateless backend API (replicas)
- Separate scheduler service (single replica recommended)
- PostgreSQL with read replicas
- Redis for caching/rate limiting

### Async I/O
- All external calls use httpx
- Non-blocking database access

### Caching Opportunities
- Provider model lists
- Search results
- Report templates
- Organization settings

### Database
- Indexed foreign keys
- Soft-delete filters
- Pagination on list endpoints

---

## Deployment Architecture

### Development

```
Docker Compose
├── backend (uvicorn)
├── frontend (vite dev server)
├── scheduler
├── redis
└── minio
```

### Production

```
Kubernetes Cluster
├── leafleter namespace
├── ingress (HTTPS)
├── backend deployment (2+ replicas)
├── frontend deployment (2+ replicas)
├── scheduler deployment (1 replica)
├── postgres statefulset
└── redis statefulset
```

### CI/CD Pipeline (Recommended)

```
Build -> Test -> Lint -> Build Images -> Push -> Deploy to Staging -> E2E Tests -> Deploy to Production
```

---

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI | Modern, async, typed, auto-docs |
| SQLAlchemy 2.x | Mature ORM, async support |
| Pydantic v2 | Validation, settings, serialization |
| React + TypeScript | Type-safe frontend ecosystem |
| TanStack Query | Server-state management |
| Zustand | Lightweight global state |
| APScheduler | Mature Python scheduler |
| SQLite dev / PostgreSQL prod | Easy local dev, robust production |
| Docker/Kubernetes | Portable deployment |

---

## Conclusion

Leafleter is built as a modular, provider-agnostic, multi-tenant SaaS platform. The architecture supports adding new AI providers, search engines, notification channels, and analysis types with minimal changes to existing code.

For setup instructions, see `setup.md`. For feature overview, see `README.md`.
