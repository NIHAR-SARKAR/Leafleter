"""Authentication endpoints."""

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import ActiveUserDep, DbDep
from app.core.logging import get_logger
from app.models import user
from app.schemas.api_key import APIKeyCreate, APIKeyPublic
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserPublic
from app.services.auth_service import auth_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    db: DbDep,
    obj_in: UserCreate,
) -> Any:
    """Register a new user and organization."""
    user = await auth_service.register(db, obj_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    db: DbDep,
    obj_in: UserLogin,
) -> Any:
    """Authenticate and receive access/refresh tokens."""
    response = await auth_service.login(db, obj_in)
    return response


@router.post("/refresh", response_model=Token)
async def refresh(
    db: DbDep,
    obj_in: RefreshTokenRequest,
) -> Any:
    """Refresh access token."""
    return await auth_service.refresh(db, obj_in.refresh_token)


@router.get("/me", response_model=UserPublic)
async def me(current_user: ActiveUserDep) -> Any:
    """Return the current authenticated user."""
    user = current_user
    return user


@router.post("/api-keys", response_model=APIKeyPublic, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    db: DbDep,
    current_user: ActiveUserDep,
    obj_in: APIKeyCreate,
) -> Any:
    """Create a new API key for the current user."""
    api_key, plain_key = await auth_service.create_api_key(
        db, obj_in=obj_in, user=current_user
    )
    return {
        **APIKeyPublic.model_validate(api_key).model_dump(),
        "plain_key": plain_key,
    }
