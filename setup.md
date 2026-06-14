# Setup Guide

This guide walks you through setting up Leafleter for local development, Docker usage, and production deployment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Local Development Setup](#local-development-setup)
4. [Docker Setup](#docker-setup)
5. [Production Deployment](#production-deployment)
6. [Database Migrations](#database-migrations)
7. [AI Provider Setup](#ai-provider-setup)
8. [Search Engine Setup](#search-engine-setup)
9. [Notification Setup](#notification-setup)
10. [Frontend Configuration](#frontend-configuration)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- Python 3.11 or higher (tested on 3.13.3)
- Node.js 20 or higher
- npm or yarn
- Git

### Optional

- Docker + Docker Compose
- PostgreSQL 15+
- Redis 7+
- Kubernetes cluster (for production)

---

## Environment Variables

Copy the example environment file and update it with your values:

```bash
cp backend/.env.example backend/.env
```

### Core Settings

| Variable                      | Default                 | Description                    |
| ----------------------------- | ----------------------- | ------------------------------ |
| `PROJECT_NAME`                | Leafleter               | Application name               |
| `VERSION`                     | 0.1.0                   | API version                    |
| `ENVIRONMENT`                 | development             | development/staging/production |
| `DEBUG`                       | False                   | Enable debug mode              |
| `API_V1_STR`                  | /api/v1                 | API base path                  |
| `SECRET_KEY`                  | change-me-in-production | JWT signing secret             |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15                      | JWT access token lifetime      |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | 7                       | Refresh token lifetime         |
| `ALGORITHM`                   | HS256                   | JWT algorithm                  |

### Database

| Variable                | Default                            | Description                       |
| ----------------------- | ---------------------------------- | --------------------------------- |
| `DATABASE_URL`          | sqlite+aiosqlite:///./leafleter.db | SQLAlchemy async URL              |
| `DATABASE_POOL_SIZE`    | 10                                 | Connection pool size (PostgreSQL) |
| `DATABASE_MAX_OVERFLOW` | 20                                 | Pool overflow (PostgreSQL)        |
| `DATABASE_ECHO`         | False                              | Log SQL queries                   |

### CORS

```env
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### AI Provider API Keys

| Variable                | Description          |
| ----------------------- | -------------------- |
| `OPENAI_API_KEY`        | OpenAI API key       |
| `AZURE_OPENAI_API_KEY`  | Azure OpenAI key     |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint       |
| `ANTHROPIC_API_KEY`     | Anthropic Claude key |
| `GOOGLE_API_KEY`        | Google Gemini key    |
| `OPENROUTER_API_KEY`    | OpenRouter key       |
| `AWS_ACCESS_KEY_ID`     | AWS access key       |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key       |
| `AWS_REGION`            | AWS region           |
| `MOONSHOT_API_KEY`      | Moonshot Kimi key    |
| `QWEN_API_KEY`          | Alibaba Qwen key     |

### Search Provider API Keys

| Variable          | Description                       |
| ----------------- | --------------------------------- |
| `SERPAPI_API_KEY` | SerpAPI key                       |
| `BING_API_KEY`    | Microsoft Bing Search key         |
| `TAVILY_API_KEY`  | Tavily key                        |
| `GOOGLE_CSE_KEY`  | Google Custom Search JSON API key |
| `GOOGLE_CSE_CX`   | Google Custom Search Engine ID    |

### Notifications

| Variable        | Description          |
| --------------- | -------------------- |
| `SMTP_HOST`     | SMTP server host     |
| `SMTP_PORT`     | SMTP port            |
| `SMTP_USER`     | SMTP username        |
| `SMTP_PASSWORD` | SMTP password        |
| `SMTP_TLS`      | Use TLS              |
| `SMTP_FROM`     | Default sender email |

### Scheduler

| Variable                  | Default | Description                        |
| ------------------------- | ------- | ---------------------------------- |
| `SCHEDULER_ENABLED`       | True    | Enable background scheduler        |
| `SCHEDULER_MAX_INSTANCES` | 3       | Max concurrent scheduler instances |
| `SCHEDULER_MAX_WORKERS`   | 5       | Max scheduler workers              |

### Rate Limiting

| Variable             | Default                  | Description          |
| -------------------- | ------------------------ | -------------------- |
| `RATE_LIMIT_ENABLED` | False                    | Enable rate limiting |
| `RATE_LIMIT_DEFAULT` | 100/minute               | Default rate limit   |
| `REDIS_URL`          | redis://localhost:6379/0 | Redis URL            |

### Object Storage

| Variable           | Default        | Description      |
| ------------------ | -------------- | ---------------- |
| `STORAGE_PROVIDER` | local          | local/minio/s3   |
| `STORAGE_BUCKET`   | leafleter      | Bucket name      |
| `MINIO_ENDPOINT`   | localhost:9000 | MinIO endpoint   |
| `MINIO_ACCESS_KEY` | minioadmin     | MinIO access key |
| `MINIO_SECRET_KEY` | minioadmin     | MinIO secret key |

### Frontend

| Variable       | Default                      | Description     |
| -------------- | ---------------------------- | --------------- |
| `VITE_API_URL` | http://localhost:8085/api/v1 | Backend API URL |

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone <repo-url>
cd Marketo
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Apply database migrations (SQLite auto-creates)
alembic upgrade head
```

### Step 3: Run Backend

```bash
uvicorn app.main:app --reload --port 8085
```

If port 8085 is blocked, use another port:

```bash
uvicorn app.main:app --reload --port 8085
```

### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Step 5: Verify

- Open frontend: `http://localhost:5173`
- Open API docs: `http://localhost:8085/docs`
- Register a new user
- Create your first topic

---

## Docker Setup

### Development

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Services started:

- Backend API: `http://localhost:8085`
- Frontend: `http://localhost:5173`
- MinIO Console: `http://localhost:9001`
- Redis: `localhost:6379`

### Production

```bash
# Copy and fill environment
cp backend/.env.example .env

# Edit .env with production values
# Then run production stack
docker compose -f docker-compose.prod.yml up --build -d
```

---

## Production Deployment

### Checklist

- [ ] Change `SECRET_KEY` to a cryptographically secure random value
- [ ] Set `ENVIRONMENT=production`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure Redis for rate limiting and caching
- [ ] Enable HTTPS and set correct `CORS_ORIGINS`
- [ ] Configure object storage (S3/MinIO)
- [ ] Set up SMTP for email notifications
- [ ] Add monitoring with Prometheus/Grafana
- [ ] Enable structured logging
- [ ] Set up backups for PostgreSQL and storage
- [ ] Configure AI provider keys
- [ ] Add search provider keys
- [ ] Run migrations before starting app

### Kubernetes Deployment

```bash
cd infra/k8s

# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Configure ConfigMap and Secret
kubectl apply -f configmap.yaml
# Edit secret.yaml with base64-encoded values
kubectl apply -f secret.yaml

# 3. Deploy database and cache
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml

# 4. Deploy backend and scheduler
kubectl apply -f backend.yaml
kubectl apply -f scheduler.yaml

# 5. Deploy frontend
kubectl apply -f frontend.yaml

# 6. Configure ingress
kubectl apply -f ingress.yaml
```

Run migrations from a backend pod:

```bash
kubectl exec -it deploy/leafleter-backend -- alembic upgrade head
```

---

## Database Migrations

### Initialize Alembic (already done)

```bash
cd backend
alembic init alembic
```

### Create New Migration

```bash
alembic revision --autogenerate -m "add user preferences"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Downgrade

```bash
alembic downgrade -1
```

### View Current Version

```bash
alembic current
```

---

## AI Provider Setup

### OpenAI (Recommended for Initial Setup)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.env`:

```env
OPENAI_API_KEY=sk-...
```

3. Register provider via UI or API:

```bash
curl -X POST http://localhost:8085/api/v1/providers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "openai",
    "name": "OpenAI GPT-4o",
    "api_key": "sk-...",
    "default_model": "gpt-4o-mini",
    "is_default": true
  }'
```

### Other Providers

Each provider follows the same registration pattern. For stub providers, registration validates configuration; live SDK calls must be enabled in the adapter.

---

## Search Engine Setup

### SerpAPI (Recommended)

1. Sign up at [SerpApi](https://serpapi.com/)
2. Get API key
3. Add to `.env`:

```env
SERPAPI_API_KEY=...
```

### Google Custom Search Engine

1. Create a CSE at [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Enable JSON API in [Google Cloud Console](https://console.cloud.google.com/)
3. Add keys:

```env
GOOGLE_CSE_KEY=...
GOOGLE_CSE_CX=...
```

### Tavily

1. Sign up at [Tavily](https://tavily.com/)
2. Add key:

```env
TAVILY_API_KEY=...
```

---

## Notification Setup

### Email (SMTP)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
SMTP_FROM=noreply@yourdomain.com
```

### Slack

1. Create an incoming webhook at [Slack API](https://api.slack.com/messaging/webhooks)
2. Use the webhook URL when creating notification configurations.

### Microsoft Teams

1. Create an incoming webhook in Teams channel
2. Use the webhook URL when configuring notifications.

### Discord

1. Create a webhook in Discord server settings
2. Use the webhook URL.

---

## Frontend Configuration

### Environment Variables

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8085/api/v1
```

For production:

```env
VITE_API_URL=https://api.yourdomain.com/api/v1
```

### Build for Production

```bash
cd frontend
npm install
npm run build
```

Output is in `frontend/dist/`.

---

## Troubleshooting

### Port 8085 is blocked

Use a different port:

```bash
uvicorn app.main:app --reload --port 8085
```

And update `VITE_API_URL` accordingly.

### SQLite pool errors

SQLite disables connection pooling in development automatically.

### Frontend build fails with chunk size warning

This is a warning, not an error. To reduce chunk size, split large vendor bundles or run:

```bash
npm run build
```

### npm audit vulnerabilities

Run:

```bash
npm audit fix
```

Or update individual packages.

### Database locked (SQLite)

Use PostgreSQL for concurrent workloads.

### Provider registration fails

- Check API key is valid
- Verify provider type is supported
- Review backend logs for detailed error

### Scheduler not running

Ensure `SCHEDULER_ENABLED=true` and only one scheduler instance is running in production.

### Background tasks timeout

For long-running dev servers, background task timeout is expected. Use production deployment or run jobs via scheduler.

---

## Next Steps

After setup:

1. Register your first organization
2. Configure an AI provider
3. Add a search provider
4. Create a topic
5. Run analysis
6. Generate a report
7. Set up schedules and alerts

For architecture details, see `architecture.md`.
