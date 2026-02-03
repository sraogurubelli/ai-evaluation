"""Error handling and custom exceptions."""

import logging
from typing import Any

import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error (400)."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(APIError):
    """Resource not found error (404)."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class UnauthorizedError(APIError):
    """Unauthorized error (401)."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(APIError):
    """Forbidden error (403)."""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class ConflictError(APIError):
    """Conflict error (409)."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error (503)."""
    
    def __init__(self, message: str = "Service temporarily unavailable", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
        )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str
    error_code: str
    message: str
    details: dict[str, Any] = {}
    request_id: str | None = None


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        "API error",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException."""
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail or "An error occurred",
            request_id=request_id,
        ).model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    # Don't expose internal error details in production
    import os
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    message = "An internal error occurred"
    if not is_production:
        message = f"Internal error: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            error_code="INTERNAL_ERROR",
            message=message,
            request_id=request_id,
        ).model_dump(),
    )
