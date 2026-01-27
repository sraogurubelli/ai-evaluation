"""Tests for sinks."""

import tempfile
from pathlib import Path
import json
import pytest
from ai_evolution.sinks.csv import CSVSink
from ai_evolution.sinks.json import JSONSink
from ai_evolution.sinks.stdout import StdoutSink
from ai_evolution.core.types import ExperimentRun, Score, DatasetItem


class TestCSVSink:
    """Tests for CSV sink."""
    
    def test_emit_run(self, tmp_path):
        """Test emitting experiment run to CSV."""
        csv_path = tmp_path / "results.csv"
        sink = CSVSink(csv_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
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
    
    def test_ml_infra_compatibility(self, tmp_path):
        """Test CSV output matches ml-infra format."""
        csv_path = tmp_path / "results.csv"
        sink = CSVSink(csv_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
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
        
        # Check column structure matches ml-infra format
        content = csv_path.read_text()
        lines = content.split("\n")
        assert "test_id" in lines[0] or "deep_diff_v3" in lines[0]


class TestJSONSink:
    """Tests for JSON sink."""
    
    def test_emit_run(self, tmp_path):
        """Test emitting experiment run to JSON."""
        json_path = tmp_path / "results.json"
        sink = JSONSink(json_path)
        
        run = ExperimentRun(
            experiment_id="exp-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1"),
            ],
        )
        
        sink.emit_run(run)
        sink.flush()
        
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert data["experiment_id"] == "exp-001"
        assert len(data["scores"]) == 1


class TestStdoutSink:
    """Tests for stdout sink."""
    
    def test_emit_run(self, capsys):
        """Test emitting experiment run to stdout."""
        sink = StdoutSink()
        
        run = ExperimentRun(
            experiment_id="exp-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1"),
            ],
        )
        
        sink.emit_run(run)
        sink.flush()
        
        captured = capsys.readouterr()
        assert "exp-001" in captured.out or "deep_diff_v1" in captured.out
