"""Usage analytics Pydantic schemas."""

from pydantic import BaseModel, ConfigDict


class DailyCost(BaseModel):
    """Cost and token totals for a single day."""

    date: str
    input_cost: float
    output_cost: float
    total_cost: float
    total_tokens: int


class ProviderCost(BaseModel):
    """Aggregated cost and token totals for a provider type."""

    provider_type: str
    total_cost: float
    total_tokens: int


class UsageCostsResponse(BaseModel):
    """Usage cost analytics for an organization."""

    daily: list[DailyCost]
    by_provider: list[ProviderCost]
