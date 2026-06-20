"""Alert rule evaluation and alert management service."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.base import BaseRepository
from app.models.alert import Alert, AlertRule
from app.models.user import User
from app.services.intelligence_hooks import on_alert_created
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate
from app.schemas.notification import NotificationCreate
from app.services.notification_service import notification_service

logger = get_logger(__name__)


class AlertService:
    """Service for alert rules and triggered alerts."""

    async def create_rule(
        self,
        db: AsyncSession,
        *,
        obj_in: AlertRuleCreate,
        user: User,
    ) -> AlertRule:
        """Create an alert rule."""
        repo = BaseRepository(AlertRule)
        rule = await repo.create(
            db,
            obj_in={
                **obj_in.model_dump(),
                "organization_id": user.organization_id,
                "is_active": True,
            },
        )
        await db.commit()
        await db.refresh(rule)
        logger.info("alert_rule_created", rule_id=rule.id)
        return rule

    async def update_rule(
        self,
        db: AsyncSession,
        *,
        rule: AlertRule,
        obj_in: AlertRuleUpdate,
    ) -> AlertRule:
        """Update an alert rule."""
        repo = BaseRepository(AlertRule)
        rule = await repo.update(
            db, db_obj=rule, obj_in=obj_in.model_dump(exclude_unset=True)
        )
        await db.commit()
        await db.refresh(rule)
        return rule

    async def delete_rule(
        self,
        db: AsyncSession,
        *,
        rule: AlertRule,
    ) -> None:
        """Delete an alert rule."""
        repo = BaseRepository(AlertRule)
        await repo.delete(db, db_obj=rule)
        await db.commit()

    async def evaluate_rules_for_run(
        self,
        db: AsyncSession,
        *,
        run: Any,
        organization_id: int,
    ) -> list[Alert]:
        """Evaluate alert rules against an analysis run."""
        result = await db.execute(
            select(AlertRule).where(
                AlertRule.organization_id == organization_id,
                AlertRule.is_active.is_(True),
                AlertRule.deleted_at.is_(None),
            )
        )
        rules = result.scalars().all()
        triggered: list[Alert] = []

        for rule in rules:
            for analysis_result in run.results:
                if analysis_result.result_type != rule.metric:
                    continue
                value = analysis_result.score
                if value is None:
                    continue
                if self._condition_met(value, rule.condition, rule.threshold):
                    alert = await self._trigger_alert(
                        db, rule=rule, value=value, run=run
                    )
                    triggered.append(alert)

        return triggered

    def _condition_met(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate a numeric condition."""
        if condition == "gt":
            return value > threshold
        if condition == "lt":
            return value < threshold
        if condition == "gte":
            return value >= threshold
        if condition == "lte":
            return value <= threshold
        if condition == "eq":
            return value == threshold
        return False

    async def _trigger_alert(
        self,
        db: AsyncSession,
        *,
        rule: AlertRule,
        value: float,
        run: Any,
    ) -> Alert:
        """Create an alert and dispatch notifications."""
        repo = BaseRepository(Alert)

        if rule.last_triggered_at:
            cooldown = timedelta(minutes=rule.cooldown_minutes)
            if datetime.now(timezone.utc) - rule.last_triggered_at < cooldown:
                logger.info("alert_cooldown_active", rule_id=rule.id)
                return Alert(
                    title="Cooldown",
                    rule_id=rule.id,
                    organization_id=rule.organization_id,
                )

        alert = await repo.create(
            db,
            obj_in={
                "title": f"Alert: {rule.name}",
                "message": f"{rule.metric} is {value} ({rule.condition} {rule.threshold})",
                "severity": "warning",
                "metric_value": value,
                "rule_id": rule.id,
                "organization_id": rule.organization_id,
                "status": "open",
            },
        )
        rule.last_triggered_at = datetime.now(timezone.utc)
        db.add(rule)
        await db.commit()
        await db.refresh(alert)

        if rule.notification_channels:
            for channel in rule.notification_channels.split(","):
                channel = channel.strip()
                if not channel:
                    continue
                await notification_service.send_notification(
                    db,
                    obj_in=NotificationCreate(
                        channel=channel,
                        recipient=rule.organization.billing_email or "admin@example.com",
                        subject=alert.title,
                        body=alert.message,
                    ),
                    organization_id=rule.organization_id,
                )

        logger.info("alert_triggered", alert_id=alert.id, rule_id=rule.id)
        try:
            on_alert_created(alert)
        except Exception as exc:
            logger.warning("intelligence_alert_created_hook_failed", error=str(exc))
        return alert


alert_service = AlertService()
