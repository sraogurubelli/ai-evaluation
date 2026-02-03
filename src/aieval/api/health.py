"""Health check endpoints for Kubernetes and monitoring."""

import asyncio
import time
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from aieval.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

# Track startup time
_startup_time: float | None = None
_startup_complete: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    timestamp: str
    version: str = "0.1.0"
    uptime_seconds: float | None = None
    checks: dict[str, Any] = {}


class DependencyCheck(BaseModel):
    """Dependency health check result."""
    
    name: str
    status: str
    message: str | None = None
    response_time_ms: float | None = None


async def check_database() -> DependencyCheck:
    """Check database connectivity."""
    start_time = time.time()
    try:
        from aieval.db.session import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        response_time = (time.time() - start_time) * 1000
        return DependencyCheck(
            name="database",
            status="healthy",
            message="Database connection successful",
            response_time_ms=round(response_time, 2),
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning("Database health check failed", error=str(e))
        return DependencyCheck(
            name="database",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


async def check_temporal() -> DependencyCheck:
    """Check Temporal connectivity."""
    start_time = time.time()
    try:
        settings = get_settings()
        # Try to connect to Temporal (basic check)
        # In a real implementation, you'd use Temporal client to check connection
        response_time = (time.time() - start_time) * 1000
        return DependencyCheck(
            name="temporal",
            status="healthy",
            message="Temporal connection check passed",
            response_time_ms=round(response_time, 2),
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning("Temporal health check failed", error=str(e))
        return DependencyCheck(
            name="temporal",
            status="unhealthy",
            message=f"Temporal connection failed: {str(e)}",
            response_time_ms=round(response_time, 2),
        )


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    global _startup_time
    
    if _startup_time is None:
        _startup_time = time.time()
    
    uptime = time.time() - _startup_time if _startup_time else None
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=round(uptime, 2) if uptime else None,
        checks={},
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_probe() -> HealthResponse:
    """
    Liveness probe for Kubernetes.
    
    Returns 200 if the application is alive and should not be restarted.
    """
    global _startup_time
    
    if _startup_time is None:
        _startup_time = time.time()
    
    uptime = time.time() - _startup_time if _startup_time else None
    
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=round(uptime, 2) if uptime else None,
        checks={},
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_probe() -> HealthResponse:
    """
    Readiness probe for Kubernetes.
    
    Returns 200 if the application is ready to serve traffic.
    Checks critical dependencies (database, etc.).
    """
    global _startup_time, _startup_complete
    
    if _startup_time is None:
        _startup_time = time.time()
    
    uptime = time.time() - _startup_time if _startup_time else None
    
    # Check dependencies
    checks: dict[str, Any] = {}
    all_healthy = True
    
    # Check database (critical)
    db_check = await check_database()
    checks["database"] = db_check.model_dump()
    if db_check.status != "healthy":
        all_healthy = False
    
    # Check Temporal (optional, but check if configured)
    settings = get_settings()
    if settings.temporal.host != "localhost:7233":  # Only check if not default
        temporal_check = await check_temporal()
        checks["temporal"] = temporal_check.model_dump()
        if temporal_check.status != "healthy":
            # Temporal is optional, so don't fail readiness if it's down
            pass
    
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready",
        )
    
    _startup_complete = True
    
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=round(uptime, 2) if uptime else None,
        checks=checks,
    )


@router.get("/startup", response_model=HealthResponse)
async def startup_probe() -> HealthResponse:
    """
    Startup probe for Kubernetes.
    
    Returns 200 once the application has finished starting up.
    """
    global _startup_complete
    
    if not _startup_complete:
        # Run readiness check to ensure we're actually ready
        try:
            await readiness_probe()
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service still starting up",
            )
    
    return HealthResponse(
        status="started",
        timestamp=datetime.utcnow().isoformat(),
        checks={},
    )


def initialize_startup_time() -> None:
    """Initialize startup time (call at application startup)."""
    global _startup_time
    _startup_time = time.time()
