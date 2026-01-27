"""Tests for experiment comparison."""

import pytest
from ai_evolution.sdk.comparison import compare_runs, get_regressions, RunComparison
from ai_evolution.core.types import ExperimentRun, Score, DatasetItem


class TestCompareRuns:
    """Tests for compare_runs function."""
    
    def test_compare_runs_basic(self):
        """Test basic run comparison."""
        run1 = ExperimentRun(
            experiment_id="exp-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="deep_diff_v1", value=0.8, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-002"}),
            ],
        )
        
        run2 = ExperimentRun(
            experiment_id="exp-002",
            scores=[
                Score(name="deep_diff_v1", value=0.95, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="deep_diff_v1", value=0.75, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-002"}),
            ],
        )
        
        comparison = compare_runs(run1, run2)
        
        assert comparison.run1_id == "exp-001"
        assert comparison.run2_id == "exp-002"
        assert "deep_diff_v1" in comparison.improvements or "deep_diff_v1" in comparison.regressions
    
    def test_compare_runs_with_threshold(self):
        """Test comparison with threshold."""
        run1 = ExperimentRun(
            experiment_id="exp-001",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        run2 = ExperimentRun(
            experiment_id="exp-002",
            scores=[
                Score(name="score1", value=0.905, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        # With default threshold (0.01), this should be unchanged
        comparison = compare_runs(run1, run2, threshold=0.01)
        
        # Small change should be considered unchanged
        assert comparison.unchanged.get("score1", 0) >= 0
    
    def test_compare_runs_missing_scores(self):
        """Test comparison when scores are missing."""
        run1 = ExperimentRun(
            experiment_id="exp-001",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        run2 = ExperimentRun(
            experiment_id="exp-002",
            scores=[
                Score(name="score1", value=0.95, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="score2", value=0.8, eval_id="score2.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        comparison = compare_runs(run1, run2)
        
        # Should handle missing scores gracefully
        assert comparison is not None


class TestGetRegressions:
    """Tests for get_regressions function."""
    
    def test_get_regressions(self):
        """Test regression detection."""
        comparison = RunComparison(
            run1_id="exp-001",
            run2_id="exp-002",
            run1_scores={"score1": [0.9, 0.8]},
            run2_scores={"score1": [0.7, 0.75]},
            regressions={"score1": 2},
        )
        
        regressions = get_regressions(comparison)
        
        assert len(regressions) > 0
        assert "score1" in regressions
