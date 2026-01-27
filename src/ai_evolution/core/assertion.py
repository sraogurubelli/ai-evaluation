"""Assertion system (for future granular checks)."""

from abc import ABC, abstractmethod
from typing import Any

from ai_evolution.core.types import Score


class Assertion(ABC):
    """Base interface for granular assertions."""
    
    @abstractmethod
    def check(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> bool:
        """
        Check assertion.
        
        Returns:
            True if assertion passes, False otherwise
        """
        pass
