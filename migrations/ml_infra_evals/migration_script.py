"""Migration script to convert ml-infra/evals datasets to new format."""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def migrate_dataset(
    source_dir: Path,
    output_dir: Path,
    entity_type: str | None = None,
) -> None:
    """
    Migrate ml-infra/evals dataset to new format.
    
    Args:
        source_dir: Source directory (ml-infra/evals/benchmarks/datasets)
        output_dir: Output directory for migrated datasets
        entity_type: Optional entity type filter
    """
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find index.csv
    index_file = source_dir / "index.csv"
    if not index_file.exists():
        print(f"Error: index.csv not found in {source_dir}")
        return
    
    # Read index
    import pandas as pd
    index_df = pd.read_csv(index_file)
    
    # Filter by entity type if specified
    if entity_type:
        index_df = index_df[index_df["entity_type"] == entity_type]
    
    print(f"Migrating {len(index_df)} test cases...")
    
    # Create JSONL dataset
    jsonl_items = []
    
    for _, row in index_df.iterrows():
        test_id = row["test_id"]
        entity_type_val = row["entity_type"]
        operation_type_val = row["operation_type"]
        
        # Load prompt
        prompt_file = source_dir / row["prompt_file"]
        with prompt_file.open(encoding="utf-8") as f:
            prompt = f.read()
        
        # Load expected
        expected_file = source_dir / row["expected_yaml_file"]
        with expected_file.open(encoding="utf-8") as f:
            expected_content = f.read()
        
        # Build input
        input_dict: dict[str, Any] = {
            "prompt": prompt,
            "entity_type": entity_type_val,
            "operation_type": operation_type_val,
        }
        
        # Load old YAML for updates
        if operation_type_val == "update" and row.get("old_yaml_file"):
            old_file = source_dir / row["old_yaml_file"]
            if old_file.exists():
                with old_file.open(encoding="utf-8") as f:
                    input_dict["old_yaml"] = f.read()
        
        # Build expected
        expected_dict = {
            "yaml": expected_content,
            "entity_type": entity_type_val,
        }
        
        # Build item
        item = {
            "id": test_id,
            "input": input_dict,
            "expected": expected_dict,
            "tags": row.get("tags", "").split(",") if pd.notna(row.get("tags")) else [],
            "metadata": {
                "notes": row.get("notes", ""),
                "prompt_file": str(row["prompt_file"]),
                "expected_file": str(row["expected_yaml_file"]),
            },
        }
        
        jsonl_items.append(item)
    
    # Write JSONL
    output_file = output_dir / f"dataset_{entity_type or 'all'}.jsonl"
    with output_file.open("w", encoding="utf-8") as f:
        for item in jsonl_items:
            f.write(json.dumps(item) + "\n")
    
    print(f"Migrated {len(jsonl_items)} items to {output_file}")
    
    # Copy files to output directory structure
    files_dir = output_dir / "files"
    files_dir.mkdir(exist_ok=True)
    
    for _, row in index_df.iterrows():
        # Copy prompt file
        prompt_file = source_dir / row["prompt_file"]
        if prompt_file.exists():
            dest = files_dir / row["prompt_file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(prompt_file, dest)
        
        # Copy expected file
        expected_file = source_dir / row["expected_yaml_file"]
        if expected_file.exists():
            dest = files_dir / row["expected_yaml_file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(expected_file, dest)
        
        # Copy old file if exists
        if row.get("old_yaml_file"):
            old_file = source_dir / row["old_yaml_file"]
            if old_file.exists():
                dest = files_dir / row["old_yaml_file"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_file, dest)
    
    print(f"Copied files to {files_dir}")


def main():
    parser = argparse.ArgumentParser(description="Migrate ml-infra/evals datasets")
    parser.add_argument(
        "--source-dir",
        required=True,
        help="Source directory (ml-infra/evals/benchmarks/datasets)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for migrated datasets",
    )
    parser.add_argument(
        "--entity-type",
        help="Filter by entity type (optional)",
    )
    
    args = parser.parse_args()
    
    migrate_dataset(
        source_dir=Path(args.source_dir),
        output_dir=Path(args.output_dir),
        entity_type=args.entity_type,
    )


if __name__ == "__main__":
    main()
