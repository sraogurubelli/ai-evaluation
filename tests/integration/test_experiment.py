"""Integration tests for Experiment."""

import pytest
import asyncio
from aieval.core.experiment import Experiment
from aieval.core.types import DatasetItem
from aieval.scorers.deep_diff import DeepDiffScorer


class MockAdapter:
    """Mock adapter for testing."""
    
    async def generate(self, input_data, model=None, **kwargs):
        """Return mock output."""
        return input_data.get("prompt", "")


@pytest.mark.asyncio
async def test_experiment_run():
    """Test running an experiment."""
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
    
    # Create experiment
    experiment = Experiment(
        name="test_experiment",
        dataset=dataset,
        scorers=scorers,
    )
    
    # Create adapter
    adapter = MockAdapter()
    
    # Run experiment
    run = await experiment.run(adapter=adapter, concurrency_limit=1)
    
    assert run.experiment_id == experiment.experiment_id
    assert len(run.scores) > 0


def test_experiment_compare():
    """Test comparing two experiment runs."""
    from aieval.core.types import Score
    
    # Create experiment
    experiment = Experiment(
        name="test",
        dataset=[],
        scorers=[],
    )
    
    # Create two runs
    run1 = ExperimentRun(
        experiment_id="exp1",
        run_id="run1",
        dataset_id="dataset1",
        scores=[Score(name="score1", value=0.8, eval_id="test.v1")],
    )
    
    run2 = ExperimentRun(
        experiment_id="exp1",
        run_id="run2",
        dataset_id="dataset1",
        scores=[Score(name="score1", value=0.9, eval_id="test.v1")],
    )
    
    # Compare
    comparison = experiment.compare(run1, run2)
    
    assert "score1" in comparison["score_changes"]
    assert comparison["score_changes"]["score1"]["change"] > 0  # Improvement
