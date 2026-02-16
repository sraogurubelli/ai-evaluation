"""Tests for dataset loaders."""

import json
import tempfile
from pathlib import Path

import pytest
from aieval.datasets.jsonl import load_jsonl_dataset
from aieval.datasets.index_csv import load_index_csv_dataset


def test_load_jsonl_dataset():
    """Test JSONL dataset loading."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(
            json.dumps(
                {"id": "test-001", "input": {"prompt": "test"}, "expected": {"contains": "test"}}
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {"id": "test-002", "input": {"prompt": "test2"}, "expected": {"contains": "test2"}}
            )
            + "\n"
        )
        temp_path = f.name

    try:
        items = load_jsonl_dataset(temp_path)
        assert len(items) == 2
        assert items[0].id == "test-001"
    finally:
        Path(temp_path).unlink()


def test_load_index_csv_dataset(tmp_path):
    """Test index CSV dataset loading."""
    # Create test structure
    datasets_dir = tmp_path / "datasets"
    datasets_dir.mkdir()

    pipelines_dir = datasets_dir / "pipelines" / "create"
    pipelines_dir.mkdir(parents=True)

    # Create index.csv
    index_file = datasets_dir / "index.csv"
    index_file.write_text(
        "test_id,entity_type,operation_type,prompt_file,old_yaml_file,expected_yaml_file,notes,tags,created_at\n"
        "pipeline_create_001,pipeline,create,pipelines/create/001_prompt.txt,,pipelines/create/001_expected.yaml,,,2025-01-01\n"
    )

    # Create prompt file
    prompt_file = pipelines_dir / "001_prompt.txt"
    prompt_file.write_text("Create a pipeline")

    # Create expected file
    expected_file = pipelines_dir / "001_expected.yaml"
    expected_file.write_text("pipeline:\n  name: Test Pipeline")

    # Load dataset
    items = load_index_csv_dataset(
        index_file=str(index_file),
        base_dir=str(datasets_dir),
        entity_type="pipeline",
        operation_type="create",
    )

    assert len(items) == 1
    assert items[0].id == "pipeline_create_001"
    assert items[0].input["prompt"] == "Create a pipeline"
