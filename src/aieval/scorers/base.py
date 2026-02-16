"""Base scorer interface."""

from abc import ABC, abstractmethod
from typing import Any

from aieval.core.types import Score


class Scorer(ABC):
    """Base interface for all scorers."""

    def __init__(self, name: str, eval_id: str):
        """
        Initialize scorer.

        Args:
            name: Score name (stable identifier for aggregation)
            eval_id: Evaluation ID (versioned identifier)
        """
        self.name = name
        self.eval_id = eval_id

    @abstractmethod
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score generated output against expected output.

        Args:
            generated: Generated output (YAML string, dict, etc.)
            expected: Expected output (YAML string, dict, etc.)
            metadata: Additional metadata (entity_type, test_id, etc.)

        Returns:
            Score object with evaluation result
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, eval_id={self.eval_id})"
