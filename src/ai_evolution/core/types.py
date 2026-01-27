"""Core types for the AI Evolution Platform."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Score:
    """Evaluation score with metadata."""
    
    name: str
    value: float | bool
    eval_id: str
    comment: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None  # For Langfuse linking
    observation_id: str | None = None  # For Langfuse linking
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "eval_id": self.eval_id,
            "comment": self.comment,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "observation_id": self.observation_id,
        }


@dataclass
class ExperimentRun:
    """Single execution of an experiment."""
    
    experiment_id: str
    run_id: str
    dataset_id: str
    scores: list[Score]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "scores": [score.to_dict() for score in self.scores],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DatasetItem:
    """Single item in a dataset."""
    
    id: str
    input: dict[str, Any]
    output: Any | None = None
    expected: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "input": self.input,
            "tags": self.tags,
            "metadata": self.metadata,
        }
        if self.output is not None:
            result["output"] = self.output
        if self.expected is not None:
            result["expected"] = self.expected
        return result
