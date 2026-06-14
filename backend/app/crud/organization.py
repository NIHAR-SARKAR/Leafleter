"""Organization repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.organization import Organization

logger = get_logger(__name__)


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for organization CRUD and lookups."""

    def __init__(self) -> None:
        super().__init__(Organization)

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Organization | None:
        """Fetch an organization by its slug."""
        result = await db.execute(
            select(Organization).where(
                Organization.slug == slug,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, db: AsyncSession, uuid: str) -> Organization | None:
        """Fetch an organization by its UUID."""
        result = await db.execute(
            select(Organization).where(
                Organization.uuid == uuid,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


organization_repository = OrganizationRepository()
