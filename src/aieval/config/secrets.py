"""Secrets management for AI Evolution Platform."""

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secrets with validation and optional external integration."""
    
    def __init__(self):
        """Initialize secrets manager."""
        self._secrets: dict[str, Any] = {}
        self._loaded = False
    
    def load_from_env(self) -> None:
        """Load secrets from environment variables."""
        if self._loaded:
            return
        
        # Database secrets
        self._secrets["database_url"] = os.getenv("DATABASE_URL")
        self._secrets["postgres_password"] = os.getenv("POSTGRES_PASSWORD")
        
        # API keys
        self._secrets["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        self._secrets["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
        
        # Langfuse
        self._secrets["langfuse_secret_key"] = os.getenv("LANGFUSE_SECRET_KEY")
        self._secrets["langfuse_public_key"] = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        # ML Infra
        self._secrets["chat_platform_auth_token"] = os.getenv("CHAT_PLATFORM_AUTH_TOKEN")
        
        # Security
        self._secrets["jwt_secret"] = os.getenv("JWT_SECRET")
        self._secrets["api_key"] = os.getenv("API_KEY")
        
        self._loaded = True
        logger.info("Secrets loaded from environment variables")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get secret value."""
        if not self._loaded:
            self.load_from_env()
        return self._secrets.get(key, default)
    
    def validate_required(self, keys: list[str]) -> None:
        """Validate that required secrets are present."""
        if not self._loaded:
            self.load_from_env()
        
        missing = [key for key in keys if not self._secrets.get(key)]
        if missing:
            raise ValueError(f"Missing required secrets: {', '.join(missing)}")
    
    def rotate_secret(self, key: str, new_value: Any) -> None:
        """Rotate a secret value."""
        if not self._loaded:
            self.load_from_env()
        
        old_value = self._secrets.get(key)
        self._secrets[key] = new_value
        logger.info(f"Secret '{key}' rotated", old_present=bool(old_value))


# Global secrets manager instance
_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
        _secrets_manager.load_from_env()
    return _secrets_manager


def get_secret(key: str, default: Any = None) -> Any:
    """Get secret value."""
    return get_secrets_manager().get(key, default)
