"""Task models for experiment execution."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from aieval.core.types import ExperimentRun


class TaskStatus(str, Enum):
    """Task status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task for executing an experiment."""
    
    id: str
    experiment_name: str
    config: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: "TaskResult | None" = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "experiment_name": self.experiment_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result.to_dict() if self.result else None,
            "metadata": self.metadata,
        }


@dataclass
class TaskResult:
    """Result of a completed task."""
    
    task_id: str
    experiment_run: ExperimentRun
    execution_time_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "experiment_run": self.experiment_run.to_dict(),
            "execution_time_seconds": self.execution_time_seconds,
            "metadata": self.metadata,
        }
