"""Unified LLM client using LiteLLM."""

from typing import Any
import structlog

from aieval.llm.config import LLMConfig

logger = structlog.get_logger(__name__)

# Try to import LiteLLM
try:
    import litellm
    from litellm import completion, acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not available. Install with: pip install litellm")


class LLMClient:
    """
    Unified LLM client wrapping LiteLLM.
    
    Supports Anthropic (primary) and OpenAI (fallback) with automatic retries.
    """
    
    def __init__(self, config: LLMConfig | None = None):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration (uses from_env() if None)
        """
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM is required for conversational interface. "
                "Install with: pip install 'ai-evolution[conversational]' or pip install litellm"
            )
        
        self.config = config or LLMConfig.from_env()
        self.logger = structlog.get_logger(__name__)
        
        # Set API keys in environment for LiteLLM
        if self.config.provider == "anthropic" and self.config.api_key:
            import os
            os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
        elif self.config.provider == "openai" and self.config.api_key:
            import os
            os.environ["OPENAI_API_KEY"] = self.config.api_key
    
    def _get_model_name(self) -> str:
        """Get model name for LiteLLM."""
        if self.config.provider == "anthropic":
            return f"anthropic/{self.config.model}"
        elif self.config.provider == "openai":
            return f"openai/{self.config.model}"
        else:
            return self.config.model
    
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
        **kwargs: Any,
    ) -> Any:
        """
        Chat with LLM.
        
        Args:
            messages: List of message dicts with "role" and "content"
            tools: Optional list of tool schemas for function calling
            tool_choice: "auto", "none", or "required"
            **kwargs: Additional parameters for LiteLLM
            
        Returns:
            LiteLLM response object
        """
        model = self._get_model_name()
        
        # Prepare parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": self.config.timeout,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice
        
        if self.config.base_url:
            params["api_base"] = self.config.base_url
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await acompletion(**params)
                return response
            except Exception as e:
                last_error = e
                self.logger.warning(
                    "LLM call failed, retrying",
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                    error=str(e),
                )
                if attempt < self.config.max_retries - 1:
                    continue
                else:
                    raise
        
        if last_error:
            raise last_error
    
    def chat_sync(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
        **kwargs: Any,
    ) -> Any:
        """
        Synchronous version of chat.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool schemas
            tool_choice: Tool choice mode
            **kwargs: Additional parameters
            
        Returns:
            LiteLLM response object
        """
        model = self._get_model_name()
        
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": self.config.timeout,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice
        
        if self.config.base_url:
            params["api_base"] = self.config.base_url
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = completion(**params)
                return response
            except Exception as e:
                last_error = e
                self.logger.warning(
                    "LLM call failed, retrying",
                    attempt=attempt + 1,
                    max_retries=self.config.max_retries,
                    error=str(e),
                )
                if attempt < self.config.max_retries - 1:
                    continue
                else:
                    raise
        
        if last_error:
            raise last_error
