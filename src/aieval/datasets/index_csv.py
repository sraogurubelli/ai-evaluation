"""Index CSV + file-based dataset loader (ml-infra/evals format).

This loader supports the exact format used by ml-infra/evals:
- Index CSV file with metadata
- Separate files for prompts, expected outputs, old YAMLs
- Schema context files for dashboard/knowledge_graph
- Offline mode for benchmarking pre-generated outputs
"""

import os
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from aieval.core.types import DatasetItem

logger = logging.getLogger(__name__)


def load_index_csv_dataset(
    index_file: str | Path,
    base_dir: str | Path = "benchmarks/datasets",
    entity_type: str | None = None,
    operation_type: str | None = None,
    test_id: str | None = None,
    offline: bool = False,
    actual_suffix: str = "actual",
) -> list[DatasetItem]:
    """
    Load data from entity-aware directory structure using index.csv.

    This format is used by ml-infra/evals and supports:
    - Separate files for prompts, expected outputs, old YAMLs (for updates)
    - Entity type filtering (pipeline, service, dashboard, etc.)
    - Operation type filtering (create, update, insights)
    - Offline mode (loads pre-generated actual outputs)

    Args:
        index_file: Path to index.csv file
        base_dir: Base directory containing the entity directories
        entity_type: Filter by entity type (pipeline, service, etc.)
        operation_type: Filter by operation type (create, update, insights)
        test_id: Filter by specific test_id
        offline: If True, load actual YAML files instead of calling API
        actual_suffix: Suffix for actual/generated files (default: "actual")

    Returns:
        List of DatasetItem objects
    """
    index_file = Path(index_file)
    base_dir = Path(base_dir)

    # Validate paths
    if not index_file.exists():
        raise FileNotFoundError(f"Index file not found: {index_file}")
    if not base_dir.exists():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")

    # Read index CSV
    try:
        index_df = pd.read_csv(index_file)
    except Exception as e:
        raise ValueError(f"Failed to read index CSV: {e}")

    # Validate required columns
    required_columns = [
        "test_id",
        "entity_type",
        "operation_type",
        "prompt_file",
        "expected_yaml_file",
    ]
    missing_columns = [col for col in required_columns if col not in index_df.columns]
    if missing_columns:
        raise ValueError(f"Index CSV missing required columns: {missing_columns}")

    # Filter by entity_type, operation_type, and test_id if specified
    if entity_type:
        index_df = index_df[index_df["entity_type"] == entity_type]
    if operation_type:
        index_df = index_df[index_df["operation_type"] == operation_type]
    if test_id:
        index_df = index_df[index_df["test_id"] == test_id]

    # In offline mode, pre-filter to only rows with actual YAML files
    if offline:
        valid_rows = []
        for idx, row in index_df.iterrows():
            expected_path = row["expected_yaml_file"]
            actual_path = expected_path.replace("_expected.", f"_{actual_suffix}.")
            actual_file = base_dir / actual_path
            if actual_file.exists():
                valid_rows.append(idx)
            else:
                logger.warning(f"Actual file not found for {row['test_id']}: {actual_file}")

        filtered_count = len(index_df) - len(valid_rows)
        if filtered_count > 0:
            logger.warning(f"Filtering out {filtered_count} test cases without actual YAML files")
        index_df = index_df.loc[valid_rows]

    logger.info(f"Loading {len(index_df)} test cases from index")

    # Load content from files
    items = []

    for _, row in index_df.iterrows():
        test_id_val = row["test_id"]
        entity_type_val = row["entity_type"]
        operation_type_val = row["operation_type"]
        notes = row.get("notes", "")

        # Load prompt
        prompt_file = base_dir / row["prompt_file"]
        if not prompt_file.exists():
            logger.warning(f"Prompt file not found for {test_id_val}: {prompt_file}")
            continue
        try:
            with prompt_file.open(encoding="utf-8") as f:
                prompt = f.read()
        except Exception as e:
            logger.error(f"Failed to read prompt file for {test_id_val}: {e}")
            continue

        # Load expected YAML/JSON
        expected_file = base_dir / row["expected_yaml_file"]
        if not expected_file.exists():
            logger.warning(f"Expected file not found for {test_id_val}: {expected_file}")
            continue
        try:
            with expected_file.open(encoding="utf-8") as f:
                expected_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read expected file for {test_id_val}: {e}")
            continue

        # Load old YAML for update operations
        old_yaml = None
        if operation_type_val == "update" and row.get("old_yaml_file"):
            old_file_path = row.get("old_yaml_file")
            if old_file_path and pd.notna(old_file_path):
                old_file = base_dir / old_file_path
                if old_file.exists():
                    try:
                        with old_file.open(encoding="utf-8") as f:
                            old_yaml = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read old YAML for {test_id_val}: {e}")
                else:
                    logger.warning(f"Old YAML file not found for {test_id_val}: {old_file}")

        # Load actual YAML for offline mode
        actual_content = None
        if offline:
            expected_path = row["expected_yaml_file"]
            # Handle different naming patterns: _expected.yaml -> _actual.yaml or _generated.yaml
            actual_path = expected_path.replace("_expected.", f"_{actual_suffix}.")
            actual_file = base_dir / actual_path
            if actual_file.exists():
                try:
                    with actual_file.open(encoding="utf-8") as f:
                        actual_content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read actual file for {test_id_val}: {e}")
            else:
                logger.warning(
                    f"Actual file not found for {test_id_val} (offline mode): {actual_file}"
                )

        # Build input dict (ml-infra format)
        input_dict: dict[str, Any] = {
            "prompt": prompt,
            "entity_type": entity_type_val,
            "operation_type": operation_type_val,
        }

        if old_yaml:
            input_dict["old_yaml"] = old_yaml

        # Load schema context if available (for dashboard/KG)
        # Try multiple naming patterns for schema context
        schema_context_file = expected_file.parent / expected_file.name.replace(
            "_expected.", "_schema_context."
        )
        if not schema_context_file.exists():
            # Try alternative pattern: _schema_context.json in same directory
            schema_context_file = (
                expected_file.parent
                / f"{expected_file.stem.replace('_expected', '_schema_context')}.json"
            )

        if schema_context_file.exists():
            import json

            try:
                with schema_context_file.open(encoding="utf-8") as f:
                    input_dict["schema_context"] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load schema context for {test_id_val}: {e}")

        # Build expected dict
        expected_dict: dict[str, Any] = {
            "yaml": expected_content,
            "entity_type": entity_type_val,
        }

        # Build metadata (preserve all original metadata)
        metadata: dict[str, Any] = {
            "test_id": test_id_val,
            "entity_type": entity_type_val,
            "operation_type": operation_type_val,
            "notes": notes if pd.notna(notes) else "",
            "prompt_file": str(row["prompt_file"]),
            "expected_file": str(row["expected_yaml_file"]),
        }

        # Add optional metadata fields if present
        if "old_yaml_file" in row and pd.notna(row["old_yaml_file"]):
            metadata["old_yaml_file"] = str(row["old_yaml_file"])
        if "tags" in row and pd.notna(row.get("tags")):
            metadata["tags"] = str(row["tags"])
        if "created_at" in row and pd.notna(row.get("created_at")):
            metadata["created_at"] = str(row["created_at"])

        # Add schema context path if loaded
        if "schema_context" in input_dict:
            metadata["schema_context_file"] = str(schema_context_file.relative_to(base_dir))

        # Create DatasetItem
        item = DatasetItem(
            id=test_id_val,
            input=input_dict,
            output=actual_content if offline else None,
            expected=expected_dict,
            tags=row.get("tags", "").split(",") if pd.notna(row.get("tags")) else [],
            metadata=metadata,
        )

        items.append(item)

    return items
