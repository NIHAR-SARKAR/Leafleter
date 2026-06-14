"""Custom exceptions and FastAPI exception handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception with status code and detail."""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Resource conflict."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        super().__init__(detail, status_code=status.HTTP_409_CONFLICT)


class ForbiddenException(AppException):
    """Access forbidden."""

    def __init__(self, detail: str = "Access forbidden") -> None:
        super().__init__(detail, status_code=status.HTTP_403_FORBIDDEN)


class UnauthorizedException(AppException):
    """Unauthorized access."""

    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)


class RateLimitException(AppException):
    """Rate limit exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded") -> None:
        super().__init__(detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None


def add_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> ORJSONResponse:
        logger.warning(
            "app_exception",
            detail=exc.detail,
            status_code=exc.status_code,
            path=request.url.path,
            **exc.extra,
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail, code=str(exc.status_code), extra=exc.extra
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        logger.warning(
            "validation_error",
            errors=exc.errors(),
            path=request.url.path,
        )
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                detail="Validation error",
                code="VALIDATION_ERROR",
                extra={"errors": exc.errors()},
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception) -> ORJSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="Internal server error",
                code="INTERNAL_ERROR",
            ).model_dump(),
        )

