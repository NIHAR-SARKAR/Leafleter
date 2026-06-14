"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logging import get_logger
from app.core.security import decode_token, verify_api_key
from app.crud.api_key import api_key_repository
from app.crud.user import user_repository
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as exc:
        logger.error("db_session_error", error=str(exc))
        raise
    finally:
        await session.close()


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_token_payload(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    oauth_token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> TokenPayload:
    """Resolve and validate the current authentication token or API key.

    Priority:
      1. Bearer token (JWT)
      2. OAuth2 token
      3. X-API-Key header
    """
    token: str | None = None

    if bearer and bearer.credentials:
        token = bearer.credentials
    elif oauth_token:
        token = oauth_token

    if token:
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise UnauthorizedException("Invalid or expired token") from exc
        if payload.type != "access":
            raise UnauthorizedException("Token type not allowed")
        request.state.auth_source = "jwt"
        request.state.token_payload = payload
        return payload

    if x_api_key:
        request.state.auth_source = "api_key"
        request.state.api_key = x_api_key
        # Placeholder sub will be resolved by get_current_user
        return TokenPayload(sub="api_key", type="api_key")

    raise UnauthorizedException("Authentication required")


TokenDep = Annotated[TokenPayload, Depends(get_token_payload)]


async def get_current_user(
    db: DbDep,
    request: Request,
    payload: TokenDep,
) -> User:
    """Resolve the authenticated user from JWT or API key."""
    if payload.type == "api_key":
        plain_key = request.state.api_key
        api_key = await api_key_repository.get_by_plain_key(db, plain_key)
        if api_key is None or not api_key.is_active:
            raise UnauthorizedException("Invalid API key")
        user = await user_repository.get(db, api_key.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("User inactive")
        request.state.api_key_id = api_key.id
        request.state.organization_id = str(user.organization_id)
        return user

    user = await user_repository.get(db, int(payload.sub))
    if user is None:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise UnauthorizedException("User inactive")
    request.state.organization_id = str(user.organization_id)
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_active_user(user: CurrentUserDep) -> User:
    """Ensure the user account is active."""
    if not user.is_active:
        raise ForbiddenException("User account is inactive")
    return user


ActiveUserDep = Annotated[User, Depends(require_active_user)]


async def get_current_organization_id(
    request: Request,
    user: ActiveUserDep,
) -> int:
    """Return the current user's organization ID."""
    org_id = getattr(request.state, "organization_id", None)
    if org_id is None:
        org_id = user.organization_id
    return int(org_id)


OrgIdDep = Annotated[int, Depends(get_current_organization_id)]


class PermissionChecker:
    """Dependency factory to enforce RBAC permissions."""

    def __init__(self, *permissions: str) -> None:
        self.permissions = set(permissions)

    async def __call__(self, user: ActiveUserDep) -> User:
        user_permissions = {p.name for p in user.role.permissions} if user.role else set()
        if user.is_superuser:
            return user
        if not self.permissions.issubset(user_permissions):
            logger.warning(
                "permission_denied",
                user_id=user.id,
                required=list(self.permissions),
                granted=list(user_permissions),
            )
            raise ForbiddenException("Insufficient permissions")
        return user


def require_permissions(*permissions: str) -> PermissionChecker:
    """Return a permission checker dependency."""
    return PermissionChecker(*permissions)
