"""Registry system for managing evaluation definitions.

The registry provides a YAML-based way to define evaluations, similar to ai-evals.
This allows customers to define evaluations declaratively without code changes.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class EvalRegistryEntry(BaseModel):
    """
    A single evaluation definition in the registry.
    
    Similar to ai-evals registry format, adapted for ai-evolution.
    """
    
    eval_id: str = Field(..., description="Versioned identifier (e.g., 'groundedness.v1')")
    score_name: str = Field(..., description="Stable metric name for aggregation")
    evaluator: str = Field(..., description="Path to Python module with evaluate() function")
    environments: list[str] | None = Field(None, description="Where this eval runs (local, ci, prod)")
    owner: str | None = Field(None, description="Team responsible for this eval")
    description: str | None = Field(None, description="What this eval measures")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def load_registry(path: str | Path) -> list[EvalRegistryEntry]:
    """
    Load and validate registry.yaml file.
    
    Args:
        path: Path to registry.yaml
    
    Returns:
        List of validated EvalRegistryEntry objects
    
    Raises:
        ValueError: If registry format is invalid
        ValidationError: If entries don't match schema
    
    Example:
        registry = load_registry("evals/registry.yaml")
        entry = next(e for e in registry if e.eval_id == "groundedness.v1")
    """
    path = Path(path)
    if not path.exists():
        raise ValueError(f"Registry file not found: {path}")
    
    with path.open() as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Registry must be a list, got {type(data)}")
    
    return [EvalRegistryEntry.model_validate(entry) for entry in data]
