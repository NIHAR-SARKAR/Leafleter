"""Base CRUD repository with multi-tenant awareness."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.db.base import Base

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async CRUD repository with tenant isolation and soft delete."""

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id_: int) -> ModelType | None:
        """Fetch a single record by ID, excluding soft-deleted rows."""
        result = await db.execute(
            select(self.model).where(self.model.id == id_, self.model.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id_: int) -> ModelType:
        """Fetch a record or raise NotFoundException."""
        obj = await self.get(db, id_)
        if obj is None:
            raise NotFoundException(f"{self.model.__name__} with id {id_} not found")
        return obj

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: Any | None = None,
    ) -> Sequence[ModelType]:
        """List records with optional tenant filtering and pagination."""
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        if organization_id is not None and hasattr(self.model, "organization_id"):
            stmt = stmt.where(self.model.organization_id == organization_id)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        try:
            await db.flush()
        except Exception as exc:
            logger.exception("create_failed", model=self.model.__name__, error=str(exc))
            raise ConflictException(f"Failed to create {self.model.__name__}") from exc
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        try:
            await db.flush()
        except Exception as exc:
            logger.exception("update_failed", model=self.model.__name__, error=str(exc))
            raise ConflictException(f"Failed to update {self.model.__name__}") from exc
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, db_obj: ModelType, hard: bool = False) -> None:
        """Soft delete a record by default; hard delete when requested."""
        if hard:
            await db.delete(db_obj)
        else:
            from app.db.base import now_utc

            db_obj.deleted_at = now_utc()
            db.add(db_obj)
        try:
            await db.flush()
        except Exception as exc:
            logger.exception("delete_failed", model=self.model.__name__, error=str(exc))
            raise ConflictException(f"Failed to delete {self.model.__name__}") from exc

    def _apply_tenant(
        self, stmt: Select[tuple[ModelType]], organization_id: int | None
    ) -> Select[tuple[ModelType]]:
        """Apply tenant isolation to a select statement if supported."""
        if organization_id is not None and hasattr(self.model, "organization_id"):
            stmt = stmt.where(self.model.organization_id == organization_id)
        return stmt
