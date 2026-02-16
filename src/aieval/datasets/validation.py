"""Dataset validation utilities."""

from typing import Any
import json
from pathlib import Path

from aieval.core.types import DatasetItem
import jsonschema


def validate_dataset_schema(
    dataset: list[DatasetItem],
    schema: dict[str, Any] | None = None,
    schema_file: str | Path | None = None,
) -> dict[str, Any]:
    """
    Validate dataset items against a JSON schema.

    Args:
        dataset: List of DatasetItem objects to validate
        schema: Optional JSON schema dict (if provided, schema_file is ignored)
        schema_file: Optional path to JSON schema file

    Returns:
        Dictionary with validation results:
        - valid: bool - Whether all items are valid
        - item_count: int - Total number of items
        - valid_count: int - Number of valid items
        - invalid_items: list[dict] - List of invalid items with errors
    """
    # Load schema
    if schema is None:
        if schema_file is None:
            raise ValueError("Either schema or schema_file must be provided")
        schema_path = Path(schema_file)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        with schema_path.open("r") as f:
            schema = json.load(f)

    # Validate schema itself
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid JSON schema: {e}")

    validator = jsonschema.Draft7Validator(schema)
    invalid_items = []
    valid_count = 0

    for i, item in enumerate(dataset):
        # Convert DatasetItem to dict for validation
        item_dict = item.to_dict()

        # Validate against schema
        errors = list(validator.iter_errors(item_dict))
        if errors:
            invalid_items.append(
                {
                    "index": i,
                    "id": item.id,
                    "errors": [str(e) for e in errors],
                }
            )
        else:
            valid_count += 1

    return {
        "valid": len(invalid_items) == 0,
        "item_count": len(dataset),
        "valid_count": valid_count,
        "invalid_count": len(invalid_items),
        "invalid_items": invalid_items,
    }
