"""Dashboard schemas."""

from pydantic import BaseModel

from app.schemas.usage import UsageCostsResponse


class DashboardStats(BaseModel):
    """Aggregate counts for the real-time dashboard."""

    topics: int
    competitors: int
    sources: int
    alert_rules: int
    open_alerts: int
    items: int
    facts: int


class DashboardSnapshot(BaseModel):
    """Full dashboard snapshot returned by the API and WebSocket."""

    stats: DashboardStats
    costs: UsageCostsResponse | None = None


class DashboardEvent(BaseModel):
    """Real-time event pushed to dashboard clients."""

    type: str = "snapshot"
    data: DashboardSnapshot
