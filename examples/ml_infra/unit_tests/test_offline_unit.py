"""Example: Offline unit testing (pre-generated outputs).

This example shows how to test pre-generated outputs without making API calls.
"""

import asyncio
from aieval import Experiment, DeepDiffScorer, load_index_csv_dataset
from aieval.core.types import Score


async def test_offline_single_case():
    """Test a single test case with pre-generated output."""
    
    # Load dataset in offline mode (loads pre-generated outputs)
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id="pipeline_create_001",
        offline=True,  # Enable offline mode
        actual_suffix="actual",  # Look for *_actual.yaml files
    )
    
    if len(dataset) == 0:
        print("Test case not found or no actual output file")
        return None
    
    test_case = dataset[0]
    
    # Check if output is available
    if not test_case.output:
        print(f"Test case {test_case.id} has no pre-generated output")
        return None
    
    print(f"Test ID: {test_case.id}")
    print(f"Has output: {test_case.output is not None}")
    
    # Score directly without adapter
    scorer = DeepDiffScorer(version="v3")
    score = scorer.score(
        generated=test_case.output,
        expected=test_case.expected,
        metadata=test_case.metadata,
    )
    
    print(f"Score: {score.value}")
    print(f"Comment: {score.comment}")
    
    return score


async def test_offline_suite():
    """Test a suite of pre-generated outputs."""
    
    # Load dataset in offline mode
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        offline=True,
        actual_suffix="actual",
    )
    
    print(f"Loaded {len(dataset)} test cases")
    
    if len(dataset) == 0:
        print("No test cases found")
        return []
    
    # Filter to only cases with outputs
    cases_with_outputs = [item for item in dataset if item.output]
    print(f"Found {len(cases_with_outputs)} test cases with pre-generated outputs")
    
    if len(cases_with_outputs) == 0:
        print("No test cases have pre-generated outputs")
        return []
    
    # Score all cases
    scorer = DeepDiffScorer(version="v3")
    scores = []
    
    for test_case in cases_with_outputs:
        score = scorer.score(
            generated=test_case.output,
            expected=test_case.expected,
            metadata=test_case.metadata,
        )
        scores.append((test_case.id, score))
    
    # Print results
    print("\nResults:")
    for test_id, score in scores:
        status = "✓" if score.value >= 0.9 else "✗"
        print(f"  {status} {test_id}: {score.value:.3f}")
    
    # Summary
    passed = sum(1 for _, score in scores if score.value >= 0.9)
    failed = len(scores) - passed
    
    print(f"\nSummary:")
    print(f"  Total: {len(scores)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    return scores


async def test_offline_with_experiment():
    """Test offline mode using Experiment (for consistency)."""
    
    # Load dataset in offline mode
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        offline=True,
        actual_suffix="actual",
    )
    
    if len(dataset) == 0:
        print("No test cases found")
        return None
    
    # Create scorer
    scorer = DeepDiffScorer(version="v3")
    
    # Create experiment (no adapter needed for offline mode)
    experiment = Experiment(
        name="offline_test",
        dataset=dataset,
        scorers=[scorer],
    )
    
    # For offline mode, we need to score items that have outputs
    # Note: The experiment.run() method expects an adapter, so we'll score manually
    scores = []
    for item in dataset:
        if item.output:
            score = scorer.score(
                generated=item.output,
                expected=item.expected,
                metadata=item.metadata,
            )
            scores.append(score)
    
    print(f"Scored {len(scores)} test cases")
    
    # Print results
    for score in scores:
        test_id = score.metadata.get("test_id", "unknown")
        print(f"  {test_id}: {score.value:.3f}")
    
    return scores


def test_offline_single_output():
    """Test a single pre-generated output directly (synchronous)."""
    
    # Example: Score a pre-generated output
    generated_yaml = """
pipeline:
  name: test-pipeline
  stages:
    - name: stage1
"""
    
    expected_yaml = """
pipeline:
  name: test-pipeline
  stages:
    - name: stage1
"""
    
    scorer = DeepDiffScorer(version="v3")
    score = scorer.score(
        generated=generated_yaml,
        expected=expected_yaml,
        metadata={"test_id": "manual_test"},
    )
    
    print(f"Score: {score.value}")
    print(f"Comment: {score.comment}")
    
    return score


if __name__ == "__main__":
    print("Example: Offline unit testing")
    print("=" * 50)
    
    # Example 1: Single offline test case
    print("\n1. Single offline test case:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_offline_single_case())
    
    # Example 2: Offline suite
    print("\n2. Offline suite:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_offline_suite())
    
    # Example 3: Offline with experiment
    print("\n3. Offline with experiment:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_offline_with_experiment())
    
    # Example 4: Direct scoring (synchronous)
    print("\n4. Direct scoring (synchronous):")
    print("-" * 50)
    test_offline_single_output()
    
    print("\nNote: Uncomment the asyncio.run() calls to execute async tests")
