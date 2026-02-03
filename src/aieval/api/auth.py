"""Authentication and authorization middleware."""

import os
from datetime import datetime, timedelta
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from aieval.config import get_settings

logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class UserRole:
    """User roles."""
    
    ADMIN = "admin"
    USER = "user"
    READ_ONLY = "read_only"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    
    if not settings.security.jwt_secret:
        raise ValueError("JWT_SECRET not configured")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            hours=settings.security.jwt_expiration_hours
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret,
        algorithm=settings.security.jwt_algorithm,
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token."""
    settings = get_settings()
    
    if not settings.security.jwt_secret:
        raise ValueError("JWT_SECRET not configured")
    
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Get and validate API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # In production, validate against database or secrets manager
    # For now, check against environment variable
    valid_api_key = os.getenv("API_KEY")
    if valid_api_key and api_key == valid_api_key:
        return api_key
    
    # If no API_KEY is set, allow in development
    settings = get_settings()
    if settings.is_development and not valid_api_key:
        logger.warning("No API_KEY set - allowing request in development mode")
        return api_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_header),
) -> dict:
    """Get current user from JWT token or API key."""
    # Try JWT token first
    if credentials:
        try:
            payload = verify_token(credentials.credentials)
            return {
                "user_id": payload.get("sub"),
                "role": payload.get("role", UserRole.USER),
                "auth_method": "jwt",
            }
        except HTTPException:
            pass
    
    # Fall back to API key
    if api_key:
        api_key_value = await get_api_key(api_key)
        return {
            "user_id": "api_key_user",
            "role": UserRole.USER,
            "auth_method": "api_key",
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_role(required_role: str):
    """Dependency to require a specific role."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", UserRole.USER)
        
        # Role hierarchy: admin > user > read_only
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.USER: 2,
            UserRole.READ_ONLY: 1,
        }
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role",
            )
        
        return current_user
    
    return role_checker


# Common dependencies
RequireAuth = Annotated[dict, Depends(get_current_user)]
RequireAdmin = Annotated[dict, Depends(require_role(UserRole.ADMIN))]
RequireUser = Annotated[dict, Depends(require_role(UserRole.USER))]
