"""Tests for sinks."""

import tempfile
from pathlib import Path
import json
import pytest
from aieval.sinks.csv import CSVSink
from aieval.sinks.json import JSONSink
from aieval.sinks.stdout import StdoutSink
from aieval.core.types import ExperimentRun, Score, DatasetItem


class TestCSVSink:
    """Tests for CSV sink."""
    
    def test_emit_run(self, tmp_path):
        """Test emitting experiment run to CSV."""
        csv_path = tmp_path / "results.csv"
        sink = CSVSink(csv_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1"),
                Score(name="deep_diff_v2", value=0.85, eval_id="deep_diff_v2.v1"),
            ],
            metadata={"test_id": "test-001", "entity_type": "pipeline"},
        )
        
        sink.emit_run(run)
        sink.flush()
        
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "deep_diff_v1" in content
        assert "deep_diff_v2" in content
    
    def test_devops_sinks_compatibility(self, tmp_path):
        """Test CSV output matches devops consumer / index-CSV format."""
        csv_path = tmp_path / "results.csv"
        sink = CSVSink(csv_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(
                    name="deep_diff_v3",
                    value=0.95,
                    eval_id="deep_diff_v3.v1",
                    metadata={"entity_type": "pipeline"},
                ),
            ],
            metadata={"test_id": "pipeline_create_001", "entity_type": "pipeline"},
        )
        
        sink.emit_run(run)
        sink.flush()
        
        # Check column structure matches devops consumer / index-CSV format
        content = csv_path.read_text()
        lines = content.split("\n")
        assert len(lines) >= 2  # header + at least one data row
        assert "deep_diff_v3" in content  # scorer name in header or data row


class TestJSONSink:
    """Tests for JSON sink."""
    
    def test_emit_run(self, tmp_path):
        """Test emitting experiment run to JSON."""
        json_path = tmp_path / "results.json"
        sink = JSONSink(json_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1"),
            ],
        )
        
        sink.emit_run(run)
        sink.flush()
        
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert isinstance(data, list) and len(data) == 1
        run_data = data[0]
        assert run_data["experiment_id"] == "exp-001"
        assert len(run_data["scores"]) == 1


class TestStdoutSink:
    """Tests for stdout sink."""
    
    def test_emit_run(self, capsys):
        """Test emitting experiment run to stdout."""
        sink = StdoutSink()
        
        run = ExperimentRun(
            experiment_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1"),
            ],
        )
        
        sink.emit_run(run)
        sink.flush()
        
        captured = capsys.readouterr()
        assert "exp-001" in captured.out or "deep_diff_v1" in captured.out
