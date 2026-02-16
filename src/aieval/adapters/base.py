"""Base adapter interface."""

from abc import ABC, abstractmethod
from typing import Any
import asyncio


class Adapter(ABC):
    """Base interface for adapters that interact with AI systems."""

    @abstractmethod
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate output from input using the AI system.

        Args:
            input_data: Input data (prompt, context, etc.)
            model: Model name (optional)
            **kwargs: Additional parameters

        Returns:
            Generated output (e.g. string, dict), or GenerateResult when the adapter
            propagates trace_id/observation_id for score linking (see docs/tracing.md).
        """
        pass

    def generate_sync(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Synchronous wrapper for generate().

        Args:
            input_data: Input data
            model: Model name (optional)
            **kwargs: Additional parameters

        Returns:
            Generated output
        """
        return asyncio.run(self.generate(input_data, model, **kwargs))

    def get_metadata(self) -> dict[str, Any]:
        """
        Return adapter metadata for introspection.

        Subclasses can override this to provide metadata about the adapter,
        such as name, version, config schema, capabilities, etc.

        Returns:
            Dictionary with adapter metadata
        """
        return {
            "name": self.__class__.__name__,
            "type": type(self).__name__,
        }
