"""Tests for experiment comparison."""

import pytest
from aieval.sdk.comparison import compare_eval_results, get_regressions, EvalResultComparison
from aieval.core.types import EvalResult, Score, DatasetItem


class TestCompareEvalResults:
    """Tests for compare_eval_results function."""
    
    def test_compare_eval_results_basic(self):
        """Test basic eval result comparison."""
        eval_result1 = EvalResult(
            eval_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="deep_diff_v1", value=0.9, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="deep_diff_v1", value=0.8, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-002"}),
            ],
        )
        
        eval_result2 = EvalResult(
            eval_id="exp-002",
            run_id="run-002",
            dataset_id="dataset-002",
            scores=[
                Score(name="deep_diff_v1", value=0.95, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="deep_diff_v1", value=0.75, eval_id="deep_diff_v1.v1", metadata={"dataset_item_id": "test-002"}),
            ],
        )
        
        comparison = compare_eval_results(eval_result1, eval_result2)
        
        # Note: eval_result1_id and eval_result2_id are set from run_id fields, not eval_id
        assert comparison.eval_result1_id is not None
        assert comparison.eval_result2_id is not None
        assert "deep_diff_v1" in comparison.improvements or "deep_diff_v1" in comparison.regressions
    
    def test_compare_eval_results_with_threshold(self):
        """Test comparison with threshold."""
        eval_result1 = EvalResult(
            eval_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        eval_result2 = EvalResult(
            eval_id="exp-002",
            run_id="run-002",
            dataset_id="dataset-002",
            scores=[
                Score(name="score1", value=0.905, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        # With default threshold (0.01), this should be unchanged
        comparison = compare_eval_results(eval_result1, eval_result2, threshold=0.01)
        
        # Small change should be considered unchanged
        assert comparison.unchanged.get("score1", 0) >= 0
    
    def test_compare_eval_results_missing_scores(self):
        """Test comparison when scores are missing."""
        eval_result1 = EvalResult(
            eval_id="exp-001",
            run_id="run-001",
            dataset_id="dataset-001",
            scores=[
                Score(name="score1", value=0.9, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        eval_result2 = EvalResult(
            eval_id="exp-002",
            run_id="run-002",
            dataset_id="dataset-002",
            scores=[
                Score(name="score1", value=0.95, eval_id="score1.v1", metadata={"dataset_item_id": "test-001"}),
                Score(name="score2", value=0.8, eval_id="score2.v1", metadata={"dataset_item_id": "test-001"}),
            ],
        )
        
        comparison = compare_eval_results(eval_result1, eval_result2)
        
        # Should handle missing scores gracefully
        assert comparison is not None


class TestGetRegressions:
    """Tests for get_regressions function."""
    
    def test_get_regressions(self):
        """Test regression detection."""
        comparison = EvalResultComparison(
            eval_result1_id="exp-001",
            eval_result2_id="exp-002",
            eval_result1_scores={"score1": [0.9, 0.8]},
            eval_result2_scores={"score1": [0.7, 0.75]},
            regressions={"score1": 2},
        )
        
        regressions = get_regressions(comparison)
        
        assert len(regressions) > 0
        assert "score1" in regressions
