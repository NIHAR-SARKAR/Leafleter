"""Provider and provider model repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.provider import Provider, ProviderModel

logger = get_logger(__name__)


class ProviderRepository(BaseRepository[Provider]):
    """Repository for AI provider configurations."""

    def __init__(self) -> None:
        super().__init__(Provider)

    async def get_default_for_organization(
        self, db: AsyncSession, organization_id: int
    ) -> Provider | None:
        """Fetch the default provider for an organization."""
        result = await db.execute(
            select(Provider)
            .where(
                Provider.organization_id == organization_id,
                Provider.is_active.is_(True),
                Provider.deleted_at.is_(None),
            )
            .order_by(Provider.fallback_order.asc(), Provider.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_by_organization(
        self,
        db: AsyncSession,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Provider]:
        """List active providers for an organization."""
        result = await db.execute(
            select(Provider)
            .where(
                Provider.organization_id == organization_id,
                Provider.deleted_at.is_(None),
            )
            .order_by(Provider.fallback_order.asc(), Provider.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class ProviderModelRepository(BaseRepository[ProviderModel]):
    """Repository for provider model definitions."""

    def __init__(self) -> None:
        super().__init__(ProviderModel)

    async def get_by_provider(
        self,
        db: AsyncSession,
        provider_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProviderModel]:
        """List models for a provider."""
        result = await db.execute(
            select(ProviderModel)
            .where(
                ProviderModel.provider_id == provider_id,
                ProviderModel.deleted_at.is_(None),
            )
            .order_by(ProviderModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_external_id(
        self, db: AsyncSession, provider_id: int, external_id: str
    ) -> ProviderModel | None:
        """Fetch a model by its external ID within a provider."""
        result = await db.execute(
            select(ProviderModel).where(
                ProviderModel.provider_id == provider_id,
                ProviderModel.external_id == external_id,
                ProviderModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


provider_repository = ProviderRepository()
provider_model_repository = ProviderModelRepository()
