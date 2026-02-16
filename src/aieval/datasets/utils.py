"""Dataset utility functions for filtering and manipulation."""

from typing import Any
from aieval.core.types import DatasetItem


def filter_dataset(
    dataset: list[DatasetItem],
    tags: list[str] | None = None,
    metadata_filters: dict[str, Any] | None = None,
) -> list[DatasetItem]:
    """
    Filter dataset by tags and/or metadata.
    
    Args:
        dataset: List of DatasetItem objects to filter
        tags: Optional list of tags - item must have ALL tags to pass
        metadata_filters: Optional dict of metadata filters
            - Simple key-value: {"key": "value"} matches items where metadata["key"] == "value"
            - Nested keys: {"key.subkey": "value"} matches items where metadata["key"]["subkey"] == "value"
            - All filters must match (AND logic)
    
    Returns:
        Filtered list of DatasetItem objects
    """
    filtered = []
    
    for item in dataset:
        # Filter by tags
        if tags:
            item_tags = set(item.tags or [])
            required_tags = set(tags)
            if not required_tags.issubset(item_tags):
                continue
        
        # Filter by metadata
        if metadata_filters:
            matches = True
            for key, expected_value in metadata_filters.items():
                # Handle nested keys (e.g., "key.subkey")
                if "." in key:
                    keys = key.split(".")
                    current = item.metadata
                    try:
                        for k in keys:
                            current = current[k]
                        if current != expected_value:
                            matches = False
                            break
                    except (KeyError, TypeError):
                        matches = False
                        break
                else:
                    # Simple key lookup
                    if item.metadata.get(key) != expected_value:
                        matches = False
                        break
            
            if not matches:
                continue
        
        filtered.append(item)
    
    return filtered
