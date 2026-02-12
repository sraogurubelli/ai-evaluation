"""Tests for DevOps consumer SDK helpers."""

import pytest
from pathlib import Path
from samples_sdk.consumers.devops import (
    create_devops_eval,
    run_devops_eval,
    compare_csv_results,
    create_devops_sinks,
)
from aieval.core.types import Run
from aieval.sinks.stdout import StdoutSink
from aieval.sinks.csv import CSVSink


class TestCreateDevOpsEval:
    """Tests for create_devops_experiment."""

    def test_create_experiment_basic(self, tmp_path):
        """Test creating DevOps experiment."""
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
        expected_file.write_text("pipeline:\n  name: Test")

        eval_ = create_devops_eval(
            index_file=str(index_file),
            base_dir=str(datasets_dir),
            entity_type="pipeline",
            operation_type="create",
        )

        assert experiment is not None
        assert len(experiment.dataset) == 1
        assert len(experiment.scorers) == 3  # v3, v2, v1

    def test_create_experiment_custom_versions(self, tmp_path):
        """Test creating experiment with custom DeepDiff versions."""
        datasets_dir = tmp_path / "datasets"
        datasets_dir.mkdir()

        index_file = datasets_dir / "index.csv"
        index_file.write_text(
            "test_id,entity_type,operation_type,prompt_file,old_yaml_file,expected_yaml_file\n"
        )

        eval_ = create_devops_eval(
            index_file=str(index_file),
            base_dir=str(datasets_dir),
            deep_diff_versions=["v3"],
        )

        assert len(experiment.scorers) == 1
        assert experiment.scorers[0].version == "v3"


class TestCompareCSVResults:
    """Tests for compare_csv_results."""

    def test_compare_csv_results_identical(self, tmp_path):
        """Test comparing identical CSV files."""
        csv1 = tmp_path / "results1.csv"
        csv2 = tmp_path / "results2.csv"

        csv1.write_text(
            "test_id,deep_diff_v1\n"
            "test-001,0.9\n"
            "test-002,0.8\n"
        )

        csv2.write_text(
            "test_id,deep_diff_v1\n"
            "test-001,0.9\n"
            "test-002,0.8\n"
        )

        comparison = compare_csv_results(csv1, csv2)

        assert comparison["csv1_rows"] == 2
        assert comparison["csv2_rows"] == 2
        assert comparison["matches"] > 0
        assert comparison["differences"] == 0

    def test_compare_csv_results_different(self, tmp_path):
        """Test comparing different CSV files."""
        csv1 = tmp_path / "results1.csv"
        csv2 = tmp_path / "results2.csv"

        csv1.write_text(
            "test_id,deep_diff_v1\n"
            "test-001,0.9\n"
        )

        csv2.write_text(
            "test_id,deep_diff_v1\n"
            "test-001,0.7\n"
        )

        comparison = compare_csv_results(csv1, csv2, tolerance=0.1)

        assert comparison["differences"] > 0

    def test_compare_csv_results_missing_file(self, tmp_path):
        """Test comparing with missing file."""
        csv1 = tmp_path / "results1.csv"
        csv2 = tmp_path / "nonexistent.csv"

        csv1.write_text("test_id,score\ntest-001,0.9\n")

        with pytest.raises(FileNotFoundError):
            compare_csv_results(csv1, csv2)


class TestCreateDevOpsSinks:
    """Tests for create_devops_sinks."""

    def test_create_sinks_default(self, tmp_path):
        """Test creating sinks with defaults."""
        sinks = create_devops_sinks(
            output_dir=str(tmp_path),
            experiment_name="test_experiment",
        )

        assert len(sinks) == 2  # Stdout + CSV
        assert any(isinstance(sink, StdoutSink) for sink in sinks)
        assert any(isinstance(sink, CSVSink) for sink in sinks)

    def test_create_sinks_no_stdout(self, tmp_path):
        """Test creating sinks without stdout."""
        sinks = create_devops_sinks(
            output_dir=str(tmp_path),
            experiment_name="test_experiment",
            include_stdout=False,
        )

        assert len(sinks) == 1  # CSV only
