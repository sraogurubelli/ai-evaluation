"""Core components for AI Evolution Platform."""

from aieval.core.types import (
    DatasetItem,
    Run,
    GenerateResult,
    Score,
    normalize_adapter_output,
)
from aieval.core.eval import Eval

__all__ = [
    "DatasetItem",
    "Run",
    "Eval",
    "GenerateResult",
    "Score",
    "normalize_adapter_output",
]
