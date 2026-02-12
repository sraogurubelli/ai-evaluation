"""Integration tests for Eval."""

import pytest
import asyncio
from aieval.core.eval import Eval
from aieval.core.types import DatasetItem, Run
from aieval.scorers.deep_diff import DeepDiffScorer


class MockAdapter:
    """Mock adapter for testing."""
    
    async def generate(self, input_data, model=None, **kwargs):
        """Return mock output."""
        return input_data.get("prompt", "")


@pytest.mark.asyncio
async def test_eval_run():
    """Test running an eval."""
    # Create dataset
    dataset = [
        DatasetItem(
            id="test-001",
            input={"prompt": "test"},
            expected={"yaml": "test: value"},
        ),
    ]

    # Create scorers
    scorers = [DeepDiffScorer(version="v1")]

    # Create eval
    eval_ = Eval(
        name="test_eval",
        dataset=dataset,
        scorers=scorers,
    )

    # Create adapter
    adapter = MockAdapter()

    # Run eval
    run = await eval_.run(adapter=adapter, concurrency_limit=1)

    assert run.eval_id == eval_.eval_id
    assert len(run.scores) > 0


def test_eval_compare():
    """Test comparing two runs."""
    from aieval.core.types import Score

    # Create eval
    eval_ = Eval(
        name="test",
        dataset=[],
        scorers=[],
    )

    # Create two runs
    run1 = Run(
        eval_id="eval1",
        run_id="run1",
        dataset_id="dataset1",
        scores=[Score(name="score1", value=0.8, eval_id="test.v1")],
    )

    run2 = Run(
        eval_id="eval1",
        run_id="run2",
        dataset_id="dataset1",
        scores=[Score(name="score1", value=0.9, eval_id="test.v1")],
    )

    # Compare
    comparison = eval_.compare(run1, run2)
    
    assert "score1" in comparison["score_changes"]
    assert comparison["score_changes"]["score1"]["change"] > 0  # Improvement
