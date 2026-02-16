"""
Base agent class that defines the interface for all evaluation agents.
"""

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Optional Langfuse import
try:
    from langfuse import observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    # Create a no-op decorator
    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


class BaseEvaluationAgent(ABC):
    """
    Abstract base class for all evaluation agent implementations.

    Attributes:
        config: Agent configuration dictionary
        logger: Logger instance for the agent
        tools: Dictionary of tools available to the agent
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        logger_name: str | None = None,
    ):
        """
        Initialize the base evaluation agent.

        Args:
            config: Agent configuration dictionary
            logger_name: Custom logger name (defaults to class name)
        """
        self.config = config or {}
        self.logger = structlog.get_logger(logger_name or self.__class__.__name__)
        self.tools: dict[str, Any] = {}
        self.agent_name = self.__class__.__name__

    @abstractmethod
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run the agent with the given query.

        Args:
            query: The query or task for the agent to process
            **kwargs: Additional parameters specific to the agent implementation

        Returns:
            The response from the agent (type depends on implementation)
        """
        pass

    def _validate_config(self, required_keys: list[str]) -> None:
        """
        Validate that required configuration keys are present.

        Args:
            required_keys: List of required configuration keys

        Raises:
            ValueError: If any required keys are missing
        """
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

    def _trace_execution(self, operation: str, **kwargs: Any):
        """
        Context manager for tracing agent execution.

        Args:
            operation: Operation name
            **kwargs: Additional metadata

        Returns:
            Context manager
        """
        if LANGFUSE_AVAILABLE:
            return observe(
                name=f"{self.agent_name}.{operation}",
                metadata={
                    "agent": self.agent_name,
                    "operation": operation,
                    **kwargs,
                },
            )
        else:
            # Return a no-op context manager
            from contextlib import nullcontext

            return nullcontext()

    def _log_execution(self, operation: str, start_time: float, **metadata: Any) -> None:
        """
        Log agent execution with timing.

        Args:
            operation: Operation name
            start_time: Start time (from time.time())
            **metadata: Additional metadata to log
        """
        duration = time.time() - start_time
        self.logger.info(
            "Agent operation completed",
            agent=self.agent_name,
            operation=operation,
            duration_seconds=duration,
            **metadata,
        )
