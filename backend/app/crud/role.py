"""Role and permission repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.role import Permission, Role

logger = get_logger(__name__)


class PermissionRepository(BaseRepository[Permission]):
    """Repository for permissions."""

    def __init__(self) -> None:
        super().__init__(Permission)

    async def get_by_name(self, db: AsyncSession, name: str) -> Permission | None:
        """Fetch a permission by its unique name."""
        result = await db.execute(
            select(Permission).where(Permission.name == name, Permission.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class RoleRepository(BaseRepository[Role]):
    """Repository for roles."""

    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_name_and_org(
        self, db: AsyncSession, name: str, organization_id: int | None
    ) -> Role | None:
        """Fetch a role by name and organization scope."""
        stmt = select(Role).where(
            Role.name == name,
            Role.deleted_at.is_(None),
            Role.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


permission_repository = PermissionRepository()
role_repository = RoleRepository()
