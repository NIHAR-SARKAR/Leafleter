"""Authentication and user management service."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictException, ForbiddenException, UnauthorizedException
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_password_hash,
    verify_password,
)
from app.crud.api_key import api_key_repository
from app.crud.organization import organization_repository
from app.crud.role import permission_repository, role_repository
from app.crud.user import user_repository
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate
from app.schemas.user import UserCreate, UserLogin
from app.utils.slug import generate_slug

logger = get_logger(__name__)

DEFAULT_PERMISSIONS: list[dict[str, str]] = [
    {"name": "topics:read", "resource": "topics", "action": "read"},
    {"name": "topics:write", "resource": "topics", "action": "write"},
    {"name": "providers:read", "resource": "providers", "action": "read"},
    {"name": "providers:write", "resource": "providers", "action": "write"},
    {"name": "reports:read", "resource": "reports", "action": "read"},
    {"name": "reports:write", "resource": "reports", "action": "write"},
    {"name": "schedules:read", "resource": "schedules", "action": "read"},
    {"name": "schedules:write", "resource": "schedules", "action": "write"},
    {"name": "integrations:read", "resource": "integrations", "action": "read"},
    {"name": "integrations:write", "resource": "integrations", "action": "write"},
    {"name": "newsletters:read", "resource": "newsletters", "action": "read"},
    {"name": "newsletters:write", "resource": "newsletters", "action": "write"},
    {"name": "alerts:read", "resource": "alerts", "action": "read"},
    {"name": "alerts:write", "resource": "alerts", "action": "write"},
    {"name": "users:read", "resource": "users", "action": "read"},
    {"name": "users:write", "resource": "users", "action": "write"},
    {"name": "billing:read", "resource": "billing", "action": "read"},
    {"name": "settings:write", "resource": "settings", "action": "write"},
]

ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "Owner": [p["name"] for p in DEFAULT_PERMISSIONS],
    "Admin": [p["name"] for p in DEFAULT_PERMISSIONS],
    "Analyst": [
        "topics:read",
        "topics:write",
        "providers:read",
        "reports:read",
        "reports:write",
        "schedules:read",
        "schedules:write",
        "integrations:read",
        "integrations:write",
        "newsletters:read",
        "newsletters:write",
        "alerts:read",
        "alerts:write",
    ],
    "Viewer": ["topics:read", "reports:read", "alerts:read", "providers:read"],
}


class AuthService:
    """Service handling authentication, registration, and API keys."""

    async def register(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """Register a new user and organization."""
        existing = await user_repository.get_by_email(db, obj_in.email)
        if existing:
            raise ConflictException("Email already registered")

        org_name = obj_in.organization_name or f"{obj_in.email.split('@')[0]}'s Organization"
        slug = generate_slug(org_name)
        slug_candidate = slug
        counter = 1
        while await organization_repository.get_by_slug(db, slug_candidate):
            slug_candidate = f"{slug}-{counter}"
            counter += 1

        org = await organization_repository.create(
            db,
            obj_in={
                "name": org_name,
                "slug": slug_candidate,
                "plan": "free",
                "is_active": True,
            },
        )
        await db.flush()

        await self._seed_organization_roles(db, org.id)
        role = await role_repository.get_by_name_and_org(db, "Owner", org.id)
        role_id = role.id if role else None

        hashed_password = get_password_hash(obj_in.password)
        user_data = obj_in.model_dump(exclude={"password", "organization_name"})
        user_data["hashed_password"] = hashed_password
        user_data["organization_id"] = org.id
        user_data["role_id"] = role_id
        user_data["is_superuser"] = False

        user = await user_repository.create(db, obj_in=user_data)
        await db.commit()
        await db.refresh(user)
        logger.info("user_registered", user_id=user.id, organization_id=org.id)
        return user

    async def login(self, db: AsyncSession, obj_in: UserLogin) -> dict[str, Any]:
        """Authenticate a user and return tokens."""
        user = await user_repository.get_by_email(db, obj_in.email)
        if user is None or not user.hashed_password:
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise ForbiddenException("Account is inactive")
        if not verify_password(obj_in.password, user.hashed_password):
            logger.warning("failed_login_attempt", email=obj_in.email)
            raise UnauthorizedException("Invalid credentials")

        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        logger.info("user_login", user_id=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict[str, Any]:
        """Refresh an access token using a refresh token."""
        payload = decode_token(refresh_token)
        if payload.type != "refresh":
            raise UnauthorizedException("Invalid token type")
        user = await user_repository.get(db, int(payload.sub))
        if user is None or not user.is_active:
            raise UnauthorizedException("User inactive")
        access_token = create_access_token(subject=user.id)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    async def create_api_key(
        self,
        db: AsyncSession,
        *,
        obj_in: APIKeyCreate,
        user: User,
    ) -> tuple[APIKey, str]:
        """Create an API key for a user."""
        plain_key, hashed_key = generate_api_key()
        prefix = plain_key.split("_")[1][:8]
        data = {
            "name": obj_in.name,
            "key_prefix": prefix,
            "hashed_key": hashed_key,
            "user_id": user.id,
            "organization_id": user.organization_id,
            "scopes": ",".join(obj_in.scopes) if obj_in.scopes else None,
            "expires_at": obj_in.expires_at,
            "is_active": True,
        }
        api_key = await api_key_repository.create(db, obj_in=data)
        return api_key, plain_key

    async def _seed_organization_roles(self, db: AsyncSession, organization_id: int) -> None:
        """Seed default permissions and roles for a new organization."""
        permission_map: dict[str, Any] = {}
        for perm_data in DEFAULT_PERMISSIONS:
            perm = await permission_repository.get_by_name(db, perm_data["name"])
            if perm is None:
                perm = await permission_repository.create(db, obj_in=perm_data)
            permission_map[perm.name] = perm

        for role_name, perm_names in ROLE_PERMISSION_MAP.items():
            existing = await role_repository.get_by_name_and_org(db, role_name, organization_id)
            if existing:
                continue
            role = await role_repository.create(
                db,
                obj_in={
                    "name": role_name,
                    "description": f"{role_name} role",
                    "is_system": True,
                    "organization_id": organization_id,
                },
            )
            role.permissions = [permission_map[name] for name in perm_names if name in permission_map]
            db.add(role)
        await db.flush()


auth_service = AuthService()
