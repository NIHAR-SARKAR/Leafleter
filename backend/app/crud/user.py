"""User repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.user import User

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user CRUD and lookups."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(
        self, db: AsyncSession, email: str, *, include_deleted: bool = False
    ) -> User | None:
        """Fetch a user by email address."""
        stmt = select(User).where(User.email == email)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """List users within an organization."""
        result = await db.execute(
            select(User)
            .where(
                User.organization_id == organization_id,
                User.deleted_at.is_(None),
            )
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


user_repository = UserRepository()
