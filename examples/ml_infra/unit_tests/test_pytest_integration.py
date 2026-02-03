"""Example: pytest-based unit tests.

This example shows how to use ai-evolution with pytest for CI/CD integration.
"""

import pytest
from aieval import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset


@pytest.mark.asyncio
async def test_pipeline_create_001():
    """Test single pipeline creation case."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id="pipeline_create_001",
    )
    
    # Skip if test case not found
    if len(dataset) == 0:
        pytest.skip("Test case 'pipeline_create_001' not found")
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name="test_001", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Assert score meets threshold
    assert result.scores[0].value >= 0.9, f"Score {result.scores[0].value} below threshold"


@pytest.mark.parametrize("test_id", [
    "pipeline_create_001",
    "pipeline_create_002",
    "pipeline_create_003",
])
@pytest.mark.asyncio
async def test_pipeline_creation(test_id):
    """Test multiple pipeline creation cases."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id=test_id,
    )
    
    # Skip if test case not found
    if len(dataset) == 0:
        pytest.skip(f"Test case '{test_id}' not found")
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name=f"test_{test_id}", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    assert result.scores[0].value >= 0.9, f"Test {test_id} failed with score {result.scores[0].value}"


@pytest.mark.asyncio
async def test_pipeline_creation_suite():
    """Run all pipeline creation tests."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    
    if len(dataset) == 0:
        pytest.skip("No pipeline creation test cases found")
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name="ci_pipeline_tests", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Assert all scores meet threshold
    for score in result.scores:
        test_id = score.metadata.get("test_id", "unknown")
        assert score.value >= 0.9, f"Test {test_id} failed with score {score.value}"


# Example using fixtures (requires conftest_ml_infra.py)
@pytest.mark.asyncio
async def test_with_fixtures(
    ml_infra_adapter,
    deep_diff_scorer_v3,
    index_file_path,
    base_dir_path,
):
    """Example using pytest fixtures."""
    dataset = load_index_csv_dataset(
        index_file=index_file_path,
        base_dir=base_dir_path,
        test_id="pipeline_create_001",
    )
    
    if len(dataset) == 0:
        pytest.skip("Test case not found")
    
    experiment = Experiment(
        name="fixture_test",
        dataset=dataset,
        scorers=[deep_diff_scorer_v3],
    )
    result = await experiment.run(
        adapter=ml_infra_adapter,
        model="claude-3-7-sonnet",
    )
    
    assert result.scores[0].value >= 0.9
