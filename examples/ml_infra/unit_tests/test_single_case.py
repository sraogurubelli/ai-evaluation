"""Example: Testing a single test case.

This example shows how to test a single test case using ai-evolution SDK.
"""

import asyncio
from ai_evolution import DatasetItem, Experiment, DeepDiffScorer, HTTPAdapter


async def test_single_case_example():
    """Example: Test a single test case."""
    
    # Create single test case
    test_case = DatasetItem(
        id="pipeline_create_001",
        input={"prompt": "Create a pipeline named 'test-pipeline'"},
        expected={"yaml": "pipeline:\n  name: test-pipeline"},
    )
    
    # Create scorer
    scorer = DeepDiffScorer(
        name="deep_diff_v3",
        eval_id="deep_diff_v3.v1",
        version="v3",
    )
    
    # Create adapter (configure for your API)
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        auth_token="your-token",
    )
    
    # Create experiment with single test case
    experiment = Experiment(
        name="single_case_test",
        dataset=[test_case],
        scorers=[scorer],
    )
    
    # Run experiment
    result = await experiment.run(
        adapter=adapter,
        model="claude-3-7-sonnet",
    )
    
    # Check result
    print(f"Test ID: {test_case.id}")
    print(f"Score: {result.scores[0].value}")
    print(f"Comment: {result.scores[0].comment}")
    
    # Assert score meets threshold
    assert result.scores[0].value >= 0.9, f"Score {result.scores[0].value} below threshold"
    
    return result


async def test_single_case_with_precomputed_output():
    """Example: Test a single test case with pre-computed output."""
    
    # Create single test case with output already populated
    test_case = DatasetItem(
        id="pipeline_create_001",
        input={"prompt": "Create a pipeline named 'test-pipeline'"},
        expected={"yaml": "pipeline:\n  name: test-pipeline"},
        output="pipeline:\n  name: test-pipeline",  # Pre-computed output
    )
    
    # Create scorer
    scorer = DeepDiffScorer(version="v3")
    
    # Score directly without adapter
    score = scorer.score(
        generated=test_case.output,
        expected=test_case.expected,
        metadata={"test_id": test_case.id},
    )
    
    print(f"Test ID: {test_case.id}")
    print(f"Score: {score.value}")
    
    assert score.value >= 0.9
    
    return score


if __name__ == "__main__":
    # Run examples
    print("Example 1: Single test case with adapter")
    print("-" * 50)
    # Uncomment to run (requires API server):
    # asyncio.run(test_single_case_example())
    
    print("\nExample 2: Single test case with pre-computed output")
    print("-" * 50)
    asyncio.run(test_single_case_with_precomputed_output())
