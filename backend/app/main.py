"""Leafleter FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.init_db import init_db
from app.scheduler.scheduler import scheduler_service

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    logger.info("starting_leafleter", environment=settings.ENVIRONMENT)
    await init_db()
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.start()
    yield
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.shutdown()
    logger.info("stopping_leafleter")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered market intelligence, social listening, and competitor analysis SaaS.",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Exception handlers
add_exception_handlers(app)

# Static storage for generated reports
app.mount("/storage", StaticFiles(directory=settings.LOCAL_STORAGE_PATH), name="storage")

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok", "version": settings.VERSION}


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """Readiness probe endpoint."""
    return {"status": "ready", "version": settings.VERSION}
