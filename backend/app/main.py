"""Leafleter FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.intelligence import (
    get_intelligence_core,
    init_intelligence_core,
    shutdown_intelligence_core,
)
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
    if settings.ENABLE_INTELLIGENCE_CORE:
        init_intelligence_core()
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.start()
    yield
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.shutdown()
    shutdown_intelligence_core()
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


@app.get("/health/intelligence", tags=["Health"])
async def health_intelligence() -> dict[str, Any]:
    """Intelligence core health check."""
    if not settings.ENABLE_INTELLIGENCE_CORE:
        return {"enabled": False}

    core = get_intelligence_core()
    if not core:
        return {"enabled": True, "status": "uninitialized"}

    return {
        "enabled": True,
        "entity_graph": core["entity_graph"].health_check(),
        "event_bus": core["event_bus"].health_check(),
        "workflows": len(core["workflow_engine"].get_active_workflows()),
        "pending_actions": len(core["action_engine"].get_priority_queue()),
    }
