"""JSONL dataset loader."""

import json
from pathlib import Path
from typing import Any

from aieval.core.types import DatasetItem


def load_jsonl_dataset(path: str | Path) -> list[DatasetItem]:
    """
    Load dataset from JSONL file.

    Each line must be a valid JSON object matching the DatasetItem schema.

    Args:
        path: Path to .jsonl file

    Returns:
        List of DatasetItem objects

    Raises:
        ValueError: If any line fails to parse or validate
    """
    path = Path(path)
    items = []

    with path.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                items.append(_dict_to_dataset_item(data))
            except Exception as e:
                raise ValueError(f"Error parsing line {line_num}: {e}") from e

    return items


def _dict_to_dataset_item(data: dict[str, Any]) -> DatasetItem:
    """Convert dictionary to DatasetItem."""
    return DatasetItem(
        id=data.get("id", ""),
        input=data.get("input", {}),
        output=data.get("output"),
        expected=data.get("expected"),
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
    )
