"""Tests for ML Infra SDK helpers."""

import pytest
import tempfile
from pathlib import Path
from ai_evolution.sdk.ml_infra import (
    create_ml_infra_experiment,
    run_ml_infra_eval,
    compare_csv_results,
    create_ml_infra_sinks,
)
from ai_evolution.core.types import ExperimentRun


class TestCreateMLInfraExperiment:
    """Tests for create_ml_infra_experiment."""
    
    def test_create_experiment_basic(self, tmp_path):
        """Test creating ML Infra experiment."""
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
        
        experiment = create_ml_infra_experiment(
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
        
        experiment = create_ml_infra_experiment(
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


class TestCreateMLInfraSinks:
    """Tests for create_ml_infra_sinks."""
    
    def test_create_sinks_default(self, tmp_path):
        """Test creating sinks with defaults."""
        sinks = create_ml_infra_sinks(
            output_dir=str(tmp_path),
            experiment_name="test_experiment",
        )
        
        assert len(sinks) == 2  # Stdout + CSV
        assert any(isinstance(sink, type) for sink in sinks)  # Check sink types
    
    def test_create_sinks_no_stdout(self, tmp_path):
        """Test creating sinks without stdout."""
        sinks = create_ml_infra_sinks(
            output_dir=str(tmp_path),
            experiment_name="test_experiment",
            include_stdout=False,
        )
        
        assert len(sinks) == 1  # CSV only
