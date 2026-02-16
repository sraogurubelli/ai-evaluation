"""Tests for agent-agnostic SDK unit-test helpers (score_single_output, run_single_item, assert_score_min)."""

import pytest
from aieval import (
    score_single_output,
    run_single_item,
    assert_score_min,
    DeepDiffScorer,
)
from aieval.core.types import DatasetItem, EvalResult, Score


class TestScoreSingleOutput:
    """Tests for score_single_output."""

    def test_score_single_output_yaml(self):
        """Score single YAML output."""
        scorer = DeepDiffScorer(
            name="deep_diff_v3",
            eval_id="deep_diff_v3.v1",
            version="v3",
        )
        generated = "pipeline:\n  name: my-pipeline\n"
        expected = "pipeline:\n  name: my-pipeline\n"
        score = score_single_output(
            generated=generated,
            expected=expected,
            scorer=scorer,
            metadata={"test_id": "test_001"},
        )
        assert score.name == "deep_diff_v3"
        assert score.value >= 0.0
        assert score.eval_id == "deep_diff_v3.v1"

    def test_score_single_output_with_metadata(self):
        """Score with custom metadata."""
        scorer = DeepDiffScorer(
            name="deep_diff_v3",
            eval_id="deep_diff_v3.v1",
            version="v3",
        )
        score = score_single_output(
            generated="x: 1",
            expected="x: 1",
            scorer=scorer,
            metadata={"entity_type": "pipeline", "test_id": "pipeline_001"},
        )
        assert score.metadata.get("test_id") == "pipeline_001"


class TestAssertScoreMin:
    """Tests for assert_score_min."""

    def test_assert_score_min_pass(self):
        """assert_score_min does not raise when score >= min_value."""
        from aieval.core.types import EvalResult
        result = EvalResult(
            eval_id="e1",
            run_id="r1",
            dataset_id="d1",
            scores=[Score(name="s1", value=0.95, eval_id="s1.v1")],
        )
        assert_score_min(result, min_value=0.9)
        assert_score_min(result, min_value=0.95, score_name="s1")

    def test_assert_score_min_fail_below(self):
        """assert_score_min raises when score < min_value."""
        from aieval.core.types import EvalResult
        result = EvalResult(
            eval_id="e1",
            run_id="r1",
            dataset_id="d1",
            scores=[Score(name="s1", value=0.7, eval_id="s1.v1")],
        )
        with pytest.raises(AssertionError, match="below min_value 0.9"):
            assert_score_min(result, min_value=0.9)

    def test_assert_score_min_fail_no_scores(self):
        """assert_score_min raises when result has no scores."""
        from aieval.core.types import EvalResult
        result = EvalResult(
            eval_id="e1",
            run_id="r1",
            dataset_id="d1",
            scores=[],
        )
        with pytest.raises(AssertionError, match="no scores"):
            assert_score_min(result, min_value=0.9)

    def test_assert_score_min_named_score(self):
        """assert_score_min uses score_name when provided."""
        from aieval.core.types import EvalResult
        result = EvalResult(
            eval_id="e1",
            run_id="r1",
            dataset_id="d1",
            scores=[
                Score(name="other", value=0.5, eval_id="o.v1"),
                Score(name="deep_diff_v3", value=0.92, eval_id="d.v1"),
            ],
        )
        assert_score_min(result, min_value=0.9, score_name="deep_diff_v3")
        with pytest.raises(AssertionError, match="below min_value"):
            assert_score_min(result, min_value=0.95, score_name="deep_diff_v3")


class TestRunSingleItem:
    """Tests for run_single_item (signature and doc; async test in integration)."""

    def test_run_single_item_importable(self):
        """run_single_item is callable and has expected signature."""
        import inspect

        sig = inspect.signature(run_single_item)
        params = list(sig.parameters)
        assert "dataset_item" in params
        assert "adapter" in params
        assert "scorer" in params
