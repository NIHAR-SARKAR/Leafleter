"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alert_rules,
    alerts,
    api_keys,
    auth,
    campaigns,
    chat,
    competitors,
    content,
    dashboard,
    debate,
    facts,
    integrations,
    intelligence,
    intelligence_sources,
    jobs,
    leads,
    newsletters,
    notifications,
    organizations,
    providers,
    report_comments,
    reports,
    roles,
    schedules,
    search,
    topics,
    usage,
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
    integrations.router, prefix="/integrations", tags=["Integrations"]
)
api_router.include_router(
    newsletters.router, prefix="/newsletters", tags=["Newsletters"]
)
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
api_router.include_router(
    intelligence_sources.router,
    prefix="/intelligence",
    tags=["Intelligence Sources"],
)
api_router.include_router(
    facts.router,
    prefix="/facts",
    tags=["Facts"],
)
api_router.include_router(
    usage.router,
    prefix="/usage",
    tags=["Usage"],
)
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)
