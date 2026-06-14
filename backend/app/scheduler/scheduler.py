"""APScheduler integration service."""

from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Wrapper around APScheduler for async job execution."""

    def __init__(self) -> None:
        self.scheduler: AsyncIOScheduler | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("scheduler_started")

    async def shutdown(self) -> None:
        """Shutdown the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            logger.info("scheduler_shutdown")

    def add_job(self, func: Callable[..., Any], trigger: str, **kwargs: Any) -> str:
        """Add a job to the scheduler."""
        if not self.scheduler:
            raise RuntimeError("Scheduler is not running")
        return self.scheduler.add_job(func, trigger, **kwargs).id

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        if self.scheduler:
            self.scheduler.remove_job(job_id)


scheduler_service = SchedulerService()
