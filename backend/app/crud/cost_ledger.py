"""Cost ledger repository."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.cost_ledger import CostLedger

logger = get_logger(__name__)


class CostLedgerRepository(BaseRepository[CostLedger]):
    """Repository for AI cost ledger entries."""

    def __init__(self) -> None:
        super().__init__(CostLedger)


# Global repository instance.
cost_ledger_repository = CostLedgerRepository()
