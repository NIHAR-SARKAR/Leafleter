# Leafleter Backend

FastAPI-based backend for Leafleter — the AI-powered market intelligence SaaS platform.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x (async)
- **Validation**: Pydantic v2
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Migrations**: Alembic
- **Scheduler**: APScheduler
- **Testing**: pytest + pytest-asyncio + httpx

## Project Structure

```
backend/
├── app/
│   ├── api/v1/        # API routers
│   ├── core/          # Config, security, logging, deps
│   ├── crud/          # Repository layer
│   ├── db/            # Database base, session, init
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic DTOs
│   ├── services/      # Business logic
│   ├── providers/     # AI provider adapters
│   ├── connectors/    # Social connectors
│   ├── search/        # Search engines + crawler
│   ├── analysis/      # Analysis engines
│   ├── reporting/     # Report generators
│   ├── scheduler/     # Background jobs
│   ├── notifications/ # Notification channels
│   ├── plugins/       # Plugin system
│   └── tests/         # Tests
├── alembic/           # Database migrations
└── pyproject.toml
```

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs are available at `http://localhost:8085/docs`.

## Test

```bash
python -m pytest app/tests -v
```

## Environment Variables

Key variables (see `.env.example` for full list):

- `DATABASE_URL` — SQLAlchemy database URL
- `SECRET_KEY` — JWT signing secret
- `OPENAI_API_KEY` — OpenAI API key
- `SERPAPI_API_KEY` — SerpAPI key
- `SMTP_*` — Email notification settings

## Scripts

Common commands:

```bash
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                                # Apply migrations
python -m pytest                                    # Run tests
uvicorn app.main:app --reload                       # Start dev server
```
