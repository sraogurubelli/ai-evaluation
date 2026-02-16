"""Tests for sinks."""

import tempfile
from pathlib import Path
import json
import pytest
from aieval.sinks.csv import CSVSink
from aieval.sinks.json import JSONSink
from aieval.sinks.stdout import StdoutSink
from aieval.sinks.junit import JUnitSink
from aieval.sinks.html_report import HTMLReportSink, render_run_to_html
from aieval.core.types import EvalResult, Score, DatasetItem


class TestCSVSink:
    """Tests for CSV sink."""

    def test_emit_run(self, tmp_path):
        """Test emitting experiment run to CSV."""
        csv_path = tmp_path / "results.csv"
        sink = CSVSink(csv_path)

        run = EvalResult(
            eval_id="exp-001",
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

        run = EvalResult(
            eval_id="exp-001",
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

        run = EvalResult(
            eval_id="exp-001",
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

        run = EvalResult(
            eval_id="exp-001",
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


class TestJUnitSink:
    """Tests for JUnit XML sink (reports)."""

    def test_emit_run_writes_junit_xml(self, tmp_path):
        """Test emitting run produces valid JUnit-style XML."""
        junit_path = tmp_path / "junit.xml"
        sink = JUnitSink(junit_path)
        run = EvalResult(
            eval_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(
                    name="deep_diff_v3", value=0.95, eval_id="d.v1", metadata={"test_id": "test_1"}
                ),
                Score(
                    name="deep_diff_v3", value=0.0, eval_id="d.v1", metadata={"test_id": "test_2"}
                ),
            ],
            metadata={"agent_id": "devops-agent"},
        )
        sink.emit_run(run)
        sink.flush()
        assert junit_path.exists()
        content = junit_path.read_text()
        assert "testsuite" in content and "testcase" in content
        assert "test_1" in content and "test_2" in content
        assert "failures=" in content


class TestHTMLReportSink:
    """Tests for HTML report sink (reports)."""

    def test_emit_run_writes_html_report(self, tmp_path):
        """Test emitting run produces HTML with summary and table."""
        html_path = tmp_path / "report.html"
        sink = HTMLReportSink(html_path)
        run = EvalResult(
            eval_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(
                    name="deep_diff_v3", value=0.95, eval_id="d.v1", metadata={"test_id": "test_1"}
                ),
                Score(
                    name="deep_diff_v3", value=0.0, eval_id="d.v1", metadata={"test_id": "test_2"}
                ),
            ],
            metadata={"agent_id": "devops-agent", "name": "my_exp"},
        )
        sink.emit_run(run)
        sink.flush()
        assert html_path.exists()
        content = html_path.read_text()
        assert "Evaluation Report" in content or "report" in content.lower()
        assert "Total" in content and "Passed" in content and "Failed" in content
        assert "test_1" in content and "test_2" in content
        assert "devops-agent" in content

    def test_render_run_to_html_from_dict(self):
        """Test render_run_to_html accepts run dict (for API)."""
        run_dict = {
            "run_id": "r1",
            "eval_id": "e1",
            "dataset_id": "d1",
            "scores": [
                {"name": "s1", "value": 1.0, "metadata": {"test_id": "t1"}},
            ],
            "metadata": {"agent_id": "a1"},
        }
        html = render_run_to_html(run_dict, title="Test Report")
        assert "r1" in html and "a1" in html and "Test Report" in html
        assert "Total" in html and "t1" in html
