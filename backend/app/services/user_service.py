"""User management service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.crud.organization import organization_repository
from app.crud.role import role_repository
from app.crud.user import user_repository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Service for user CRUD within an organization."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: UserCreate,
        organization_id: int,
        created_by: User,
    ) -> User:
        """Create a new user in the same organization."""
        existing = await user_repository.get_by_email(db, obj_in.email)
        if existing:
            raise ConflictException("Email already registered")

        role_id = obj_in.role_id
        if role_id:
            role = await role_repository.get(db, role_id)
            if role is None or role.organization_id != organization_id:
                raise NotFoundException("Role not found")

        user_data = obj_in.model_dump(exclude={"password", "organization_name"})
        user_data["hashed_password"] = get_password_hash(obj_in.password)
        user_data["organization_id"] = organization_id
        user_data["role_id"] = role_id
        user_data["is_superuser"] = False

        user = await user_repository.create(db, obj_in=user_data)
        await db.commit()
        await db.refresh(user)
        logger.info(
            "user_created",
            user_id=user.id,
            organization_id=organization_id,
            created_by=created_by.id,
        )
        return user

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate,
    ) -> User:
        """Update a user."""
        update_data = obj_in.model_dump(exclude_unset=True)
        if "role_id" in update_data and update_data["role_id"] is not None:
            role = await role_repository.get(db, update_data["role_id"])
            if role is None or role.organization_id != db_obj.organization_id:
                raise NotFoundException("Role not found")
        user = await user_repository.update(db, db_obj=db_obj, obj_in=update_data)
        await db.commit()
        await db.refresh(user)
        logger.info("user_updated", user_id=user.id)
        return user

    async def delete(self, db: AsyncSession, *, user: User) -> None:
        """Soft delete a user."""
        await user_repository.delete(db, db_obj=user)
        await db.commit()
        logger.info("user_deleted", user_id=user.id)


user_service = UserService()
