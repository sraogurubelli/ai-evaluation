"""Base sink interface."""

from abc import ABC, abstractmethod

from aieval.core.types import Score, EvalResult


class Sink(ABC):
    """Base interface for all sinks."""
    
    @abstractmethod
    def emit(self, score: Score) -> None:
        """Emit a single score."""
        pass
    
    @abstractmethod
    def emit_run(self, run: EvalResult) -> None:
        """Emit an entire run."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered data."""
        pass
