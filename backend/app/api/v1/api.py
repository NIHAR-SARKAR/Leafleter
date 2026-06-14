"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    alert_rules,
    api_keys,
    auth,
    campaigns,
    chat,
    competitors,
    content,
    debate,
    intelligence,
    jobs,
    leads,
    notifications,
    organizations,
    providers,
    report_comments,
    reports,
    roles,
    schedules,
    search,
    topics,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    organizations.router, prefix="/organizations", tags=["Organizations"]
)
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(topics.router, prefix="/topics", tags=["Topics"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)
api_router.include_router(alert_rules.router, prefix="/alert-rules", tags=["Alert Rules"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(
    competitors.router, prefix="/competitors", tags=["Competitors"]
)
api_router.include_router(debate.router, prefix="/debate", tags=["Debate"])
api_router.include_router(
    content.router, prefix="/content", tags=["Content Generator"]
)
api_router.include_router(
    campaigns.router, prefix="/campaigns", tags=["Campaign Analyzer"]
)
api_router.include_router(leads.router, prefix="/leads", tags=["Lead Discovery"])
api_router.include_router(
    report_comments.router, prefix="/reports", tags=["Report Comments"]
)
api_router.include_router(
    intelligence.router, prefix="/intelligence", tags=["Intelligence"]
)
