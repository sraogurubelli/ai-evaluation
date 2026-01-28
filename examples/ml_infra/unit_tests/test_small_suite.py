"""Example: Small test suite (entity/operation filtering).

This example shows how to run a small test suite filtered by entity type and operation.
"""

import asyncio
from ai_evolution import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset


async def test_pipeline_create_suite():
    """Run all pipeline create tests."""
    
    # Load all pipeline create tests
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    
    print(f"Loaded {len(dataset)} test cases")
    
    if len(dataset) == 0:
        print("No test cases found")
        return
    
    # Create scorer
    scorer = DeepDiffScorer(version="v3")
    
    # Create adapter
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    # Create experiment
    experiment = Experiment(
        name="pipeline_create_suite",
        dataset=dataset,
        scorers=[scorer],
    )
    
    # Run experiment
    result = await experiment.run(
        adapter=adapter,
        model="claude-3-7-sonnet",
        concurrency_limit=5,
    )
    
    # Print results
    print(f"\nResults:")
    print(f"Total scores: {len(result.scores)}")
    
    # Group by test_id
    scores_by_test = {}
    for score in result.scores:
        test_id = score.metadata.get("test_id", "unknown")
        if test_id not in scores_by_test:
            scores_by_test[test_id] = []
        scores_by_test[test_id].append(score)
    
    # Print per-test results
    for test_id, scores in scores_by_test.items():
        avg_score = sum(s.value for s in scores) / len(scores)
        print(f"  {test_id}: {avg_score:.3f}")
    
    # Check for failures
    failures = [
        (score.metadata.get("test_id"), score.value)
        for score in result.scores
        if score.value < 0.9
    ]
    
    if failures:
        print(f"\nFailures (score < 0.9):")
        for test_id, score_value in failures:
            print(f"  {test_id}: {score_value}")
    else:
        print("\nAll tests passed!")
    
    return result


async def test_service_update_suite():
    """Run all service update tests."""
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="service",
        operation_type="update",
    )
    
    print(f"Loaded {len(dataset)} service update test cases")
    
    if len(dataset) == 0:
        print("No test cases found")
        return
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(
        name="service_update_suite",
        dataset=dataset,
        scorers=[scorer],
    )
    
    result = await experiment.run(
        adapter=adapter,
        model="claude-3-7-sonnet",
    )
    
    print(f"Total scores: {len(result.scores)}")
    return result


async def test_dashboard_insights_suite():
    """Run all dashboard insights tests."""
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="dashboard",
        operation_type="insights",
    )
    
    print(f"Loaded {len(dataset)} dashboard insights test cases")
    
    if len(dataset) == 0:
        print("No test cases found")
        return
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(
        name="dashboard_insights_suite",
        dataset=dataset,
        scorers=[scorer],
    )
    
    result = await experiment.run(
        adapter=adapter,
        model="claude-3-7-sonnet",
    )
    
    print(f"Total scores: {len(result.scores)}")
    return result


if __name__ == "__main__":
    print("Example: Small test suite")
    print("=" * 50)
    
    # Uncomment to run (requires API server and dataset):
    # asyncio.run(test_pipeline_create_suite())
    # asyncio.run(test_service_update_suite())
    # asyncio.run(test_dashboard_insights_suite())
    
    print("\nNote: Uncomment the asyncio.run() calls to execute tests")
