"""Alert and alert rule Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertRuleBase(BaseModel):
    """Base alert rule fields."""

    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=1000)
    entity_type: str = Field(..., max_length=50)
    condition: str = Field(..., max_length=50)
    threshold: float
    metric: str = Field(..., max_length=50)
    notification_channels: str | None = Field(None, max_length=500)
    cooldown_minutes: int = 60
    configuration: dict | None = None


class AlertRuleCreate(AlertRuleBase):
    """Alert rule creation payload."""

    topic_id: int | None = None


class AlertRuleUpdate(BaseModel):
    """Alert rule update payload."""

    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    entity_type: str | None = Field(None, max_length=50)
    condition: str | None = Field(None, max_length=50)
    threshold: float | None = None
    metric: str | None = Field(None, max_length=50)
    is_active: bool | None = None
    notification_channels: str | None = Field(None, max_length=500)
    cooldown_minutes: int | None = None
    configuration: dict | None = None


class AlertRuleInDB(AlertRuleBase):
    """Alert rule database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    last_triggered_at: datetime | None
    topic_id: int | None
    organization_id: int
    created_at: datetime
    updated_at: datetime


class AlertCreate(BaseModel):
    """Alert creation payload."""

    title: str = Field(..., max_length=255)
    message: str | None = Field(None, max_length=2000)
    severity: str = "info"
    metric_value: float | None = None
    rule_id: int


class AlertInDB(AlertCreate):
    """Alert database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    acknowledged_by_user_id: int | None
    organization_id: int
    created_at: datetime
