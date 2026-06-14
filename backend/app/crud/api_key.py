"""API key repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import hash_api_key
from app.crud.base import BaseRepository
from app.models.api_key import APIKey

logger = get_logger(__name__)


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API key management."""

    def __init__(self) -> None:
        super().__init__(APIKey)

    async def get_by_plain_key(self, db: AsyncSession, plain_key: str) -> APIKey | None:
        """Find an active API key by its plaintext value.

        This scans stored hashes; intended for low-volume API key usage.
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.deleted_at.is_(None),
                APIKey.is_active.is_(True),
            )
        )
        for api_key in result.scalars().all():
            if api_key.hashed_key and hash_api_key(plain_key) == api_key.hashed_key:
                continue
            # Use bcrypt verification directly
            from app.core.security import verify_api_key

            if verify_api_key(plain_key, api_key.hashed_key):
                return api_key
        return None


api_key_repository = APIKeyRepository()
