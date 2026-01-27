"""Base sink interface."""

from abc import ABC, abstractmethod

from ai_evolution.core.types import Score, ExperimentRun


class Sink(ABC):
    """Base interface for all sinks."""
    
    @abstractmethod
    def emit(self, score: Score) -> None:
        """Emit a single score."""
        pass
    
    @abstractmethod
    def emit_run(self, run: ExperimentRun) -> None:
        """Emit an entire experiment run."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered data."""
        pass
