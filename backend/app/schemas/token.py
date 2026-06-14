"""Token-related Pydantic schemas."""

from pydantic import BaseModel


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    type: str | None = None
    exp: int | None = None


class Token(BaseModel):
    """Access and refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str
