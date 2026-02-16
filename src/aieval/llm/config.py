"""LLM configuration."""

import os
from typing import Any
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    
    provider: str = "anthropic"  # "anthropic" or "openai"
    model: str = "claude-3-5-sonnet-20241022"  # Default Anthropic model
    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 60
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Create LLMConfig from environment variables.
        
        Environment variables:
        - AIEVAL_LLM_PROVIDER: "anthropic" or "openai" (default: "anthropic")
        - AIEVAL_LLM_MODEL: Model name (default: "claude-3-5-sonnet-20241022" for Anthropic, "gpt-4o" for OpenAI)
        - ANTHROPIC_API_KEY: Anthropic API key
        - OPENAI_API_KEY: OpenAI API key
        - AIEVAL_LLM_BASE_URL: Optional base URL for custom endpoints
        - AIEVAL_LLM_TIMEOUT: Timeout in seconds (default: 60)
        - AIEVAL_LLM_MAX_RETRIES: Max retries (default: 3)
        """
        provider = os.getenv("AIEVAL_LLM_PROVIDER", "anthropic").lower()
        
        # Set default model based on provider
        if provider == "openai":
            default_model = os.getenv("AIEVAL_LLM_MODEL", "gpt-4o")
        else:
            default_model = os.getenv("AIEVAL_LLM_MODEL", "claude-3-5-sonnet-20241022")
        
        # Get API key based on provider
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        return cls(
            provider=provider,
            model=default_model,
            api_key=api_key,
            base_url=os.getenv("AIEVAL_LLM_BASE_URL"),
            timeout=int(os.getenv("AIEVAL_LLM_TIMEOUT", "60")),
            max_retries=int(os.getenv("AIEVAL_LLM_MAX_RETRIES", "3")),
        )
