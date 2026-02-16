"""Core components for AI Evolution Platform."""

from aieval.core.types import (
    DatasetItem,
    EvalResult,
    GenerateResult,
    Score,
    normalize_adapter_output,
)
from aieval.core.eval import Eval

__all__ = [
    "DatasetItem",
    "EvalResult",
    "Eval",
    "GenerateResult",
    "Score",
    "normalize_adapter_output",
]
