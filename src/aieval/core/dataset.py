"""Dataset abstraction (for future use)."""

from typing import Protocol

from aieval.core.types import DatasetItem


class Dataset(Protocol):
    """Protocol for dataset-like objects."""
    
    def load(self) -> list[DatasetItem]:
        """Load dataset items."""
        ...
