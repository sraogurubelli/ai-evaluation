"""Expanded tests for dataset loaders."""

import json
import tempfile
from pathlib import Path
import pytest
from ai_evolution.datasets.jsonl import load_jsonl_dataset
from ai_evolution.datasets.index_csv import load_index_csv_dataset
from ai_evolution.datasets.function import load_function_dataset


class TestJSONLDataset:
    """Tests for JSONL dataset loader."""
    
    def test_load_valid_jsonl(self):
        """Test loading valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"id": "test-001", "input": {"prompt": "test"}, "expected": {"contains": "test"}}) + "\n")
            f.write(json.dumps({"id": "test-002", "input": {"prompt": "test2"}, "expected": {"contains": "test2"}}) + "\n")
            temp_path = f.name
        
        try:
            items = load_jsonl_dataset(temp_path)
            assert len(items) == 2
            assert items[0].id == "test-001"
            assert items[1].id == "test-002"
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_jsonl(self):
        """Test loading empty JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name
        
        try:
            items = load_jsonl_dataset(temp_path)
            assert len(items) == 0
        finally:
            Path(temp_path).unlink()
    
    def test_load_invalid_jsonl(self):
        """Test loading invalid JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("invalid json\n")
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):
                load_jsonl_dataset(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_jsonl_with_metadata(self):
        """Test loading JSONL with metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({
                "id": "test-001",
                "input": {"prompt": "test"},
                "expected": {"contains": "test"},
                "metadata": {"entity_type": "pipeline"}
            }) + "\n")
            temp_path = f.name
        
        try:
            items = load_jsonl_dataset(temp_path)
            assert items[0].metadata.get("entity_type") == "pipeline"
        finally:
            Path(temp_path).unlink()


class TestIndexCSVDataset:
    """Tests for Index CSV dataset loader."""
    
    def test_load_with_filters(self, tmp_path):
        """Test loading with entity type and operation type filters."""
        datasets_dir = tmp_path / "datasets"
        datasets_dir.mkdir()
        
        pipelines_dir = datasets_dir / "pipelines" / "create"
        pipelines_dir.mkdir(parents=True)
        
        index_file = datasets_dir / "index.csv"
        index_file.write_text(
            "test_id,entity_type,operation_type,prompt_file,old_yaml_file,expected_yaml_file\n"
            "pipeline_create_001,pipeline,create,pipelines/create/001_prompt.txt,,pipelines/create/001_expected.yaml\n"
            "pipeline_update_001,pipeline,update,pipelines/update/001_prompt.txt,pipelines/update/001_old.yaml,pipelines/update/001_expected.yaml\n"
        )
        
        prompt_file = pipelines_dir / "001_prompt.txt"
        prompt_file.write_text("Create pipeline")
        
        expected_file = pipelines_dir / "001_expected.yaml"
        expected_file.write_text("pipeline:\n  name: Test")
        
        items = load_index_csv_dataset(
            index_file=str(index_file),
            base_dir=str(datasets_dir),
            entity_type="pipeline",
            operation_type="create",
        )
        
        assert len(items) == 1
        assert items[0].id == "pipeline_create_001"
    
    def test_load_offline_mode(self, tmp_path):
        """Test loading in offline mode with actual files."""
        datasets_dir = tmp_path / "datasets"
        datasets_dir.mkdir()
        
        pipelines_dir = datasets_dir / "pipelines" / "create"
        pipelines_dir.mkdir(parents=True)
        
        index_file = datasets_dir / "index.csv"
        index_file.write_text(
            "test_id,entity_type,operation_type,prompt_file,old_yaml_file,expected_yaml_file\n"
            "pipeline_create_001,pipeline,create,pipelines/create/001_prompt.txt,,pipelines/create/001_expected.yaml\n"
        )
        
        prompt_file = pipelines_dir / "001_prompt.txt"
        prompt_file.write_text("Create pipeline")
        
        expected_file = pipelines_dir / "001_expected.yaml"
        expected_file.write_text("pipeline:\n  name: Expected")
        
        actual_file = pipelines_dir / "001_actual.yaml"
        actual_file.write_text("pipeline:\n  name: Actual")
        
        items = load_index_csv_dataset(
            index_file=str(index_file),
            base_dir=str(datasets_dir),
            offline=True,
            actual_suffix="actual",
        )
        
        assert len(items) == 1
        # In offline mode, output should be populated from actual file
        assert items[0].output is not None


class TestFunctionDataset:
    """Tests for function-based dataset loader."""
    
    def test_load_function_dataset(self):
        """Test loading function-based dataset."""
        def generate_items():
            for i in range(3):
                yield {
                    "id": f"test-{i:03d}",
                    "input": {"prompt": f"Test {i}"},
                    "expected": {"contains": str(i)},
                }
        
        items = load_function_dataset(generate_items)
        
        assert len(items) == 3
        assert items[0].id == "test-000"
        assert items[2].id == "test-002"
    
    def test_load_empty_function_dataset(self):
        """Test loading empty function-based dataset."""
        def generate_items():
            return
            yield  # Make it a generator
        
        items = load_function_dataset(generate_items)
        
        assert len(items) == 0
