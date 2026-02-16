"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Any

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from aieval.config import get_settings

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than 1 minute."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 60

        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip] if timestamp > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]

        self.last_cleanup = current_time

    def is_allowed(self, ip: str) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        self._cleanup_old_entries()

        current_time = time.time()
        cutoff_time = current_time - 60

        # Remove old requests
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip] if timestamp > cutoff_time
        ]

        # Check limit
        request_count = len(self.requests[ip])

        if request_count >= self.requests_per_minute:
            return False, 0

        # Add current request
        self.requests[ip].append(current_time)

        remaining = self.requests_per_minute - len(self.requests[ip])
        return True, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app: Any, requests_per_minute: int = 60):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in [
            "/health",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/metrics",
        ]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        is_allowed, remaining = self.rate_limiter.is_allowed(client_ip)

        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


# Note: RateLimitMiddleware is used directly in app.py
# This function is kept for backward compatibility but not used
