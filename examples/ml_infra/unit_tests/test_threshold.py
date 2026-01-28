"""Example: Threshold-based pass/fail testing.

This example shows how to use score thresholds for pass/fail criteria in CI/CD.
"""

import asyncio
import sys
from ai_evolution import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset


async def test_with_threshold(test_id: str, threshold: float = 0.9):
    """Test a single test case with a threshold."""
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id=test_id,
    )
    
    if len(dataset) == 0:
        print(f"Test case '{test_id}' not found")
        return False
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name=f"threshold_test_{test_id}", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    score_value = result.scores[0].value
    
    print(f"Test: {test_id}")
    print(f"Score: {score_value:.3f}")
    print(f"Threshold: {threshold:.3f}")
    
    if score_value >= threshold:
        print("✓ PASS")
        return True
    else:
        print("✗ FAIL")
        return False


async def test_suite_with_threshold(
    entity_type: str | None = None,
    operation_type: str | None = None,
    threshold: float = 0.9,
):
    """Test a suite with threshold-based pass/fail."""
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type=entity_type,
        operation_type=operation_type,
    )
    
    if len(dataset) == 0:
        print("No test cases found")
        return False
    
    print(f"Running {len(dataset)} test cases...")
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(
        name="threshold_suite",
        dataset=dataset,
        scorers=[scorer],
    )
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Check all scores against threshold
    passed = 0
    failed = 0
    failures = []
    
    for score in result.scores:
        test_id = score.metadata.get("test_id", "unknown")
        if score.value >= threshold:
            passed += 1
        else:
            failed += 1
            failures.append((test_id, score.value))
    
    print(f"\nResults:")
    print(f"  Total: {len(result.scores)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failures:
        print(f"\nFailures (score < {threshold}):")
        for test_id, score_value in failures:
            print(f"  {test_id}: {score_value:.3f}")
    
    # Return False if any failures (for CI/CD exit code)
    return failed == 0


async def test_with_exit_code():
    """Example: Use exit codes for CI/CD integration."""
    
    # Run test suite
    success = await test_suite_with_threshold(
        entity_type="pipeline",
        operation_type="create",
        threshold=0.9,
    )
    
    # Exit with appropriate code
    if success:
        print("\n✓ All tests passed")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


async def test_with_custom_thresholds():
    """Example: Different thresholds for different test types."""
    
    thresholds = {
        "pipeline": 0.95,  # Higher threshold for pipelines
        "service": 0.90,    # Standard threshold for services
        "dashboard": 0.85, # Lower threshold for dashboards
    }
    
    results = {}
    
    for entity_type, threshold in thresholds.items():
        print(f"\nTesting {entity_type} (threshold: {threshold})...")
        success = await test_suite_with_threshold(
            entity_type=entity_type,
            threshold=threshold,
        )
        results[entity_type] = success
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    for entity_type, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {entity_type}: {status}")
    
    # Overall success
    overall_success = all(results.values())
    return overall_success


if __name__ == "__main__":
    print("Example: Threshold-based testing")
    print("=" * 50)
    
    # Example 1: Single test with threshold
    print("\n1. Single test with threshold:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_with_threshold("pipeline_create_001", threshold=0.9))
    
    # Example 2: Suite with threshold
    print("\n2. Suite with threshold:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_suite_with_threshold(entity_type="pipeline", operation_type="create"))
    
    # Example 3: With exit codes (for CI/CD)
    print("\n3. With exit codes (CI/CD):")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_with_exit_code())
    
    # Example 4: Custom thresholds
    print("\n4. Custom thresholds:")
    print("-" * 50)
    # Uncomment to run:
    # asyncio.run(test_with_custom_thresholds())
    
    print("\nNote: Uncomment the asyncio.run() calls to execute tests")
