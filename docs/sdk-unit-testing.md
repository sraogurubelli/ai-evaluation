# SDK Unit-Level Testing Guide

A practical guide for ML Infra agent dev teams to use ai-evolution for unit-level evaluation testing.

## Quick Start (5-minute guide)

### Installation

```bash
pip install ai-evolution
```

### Simplest Example: Single Test Case

```python
from ai_evolution import DatasetItem, DeepDiffScorer

# Create single test case
test_case = DatasetItem(
    id="pipeline_create_001",
    input={"prompt": "Create a pipeline..."},
    expected={"yaml": "pipeline:\n  name: test"},
)

# Score a single output
scorer = DeepDiffScorer(version="v3")
score = scorer.score(
    generated=generated_yaml,
    expected=test_case.expected,
    metadata={"test_id": test_case.id}
)

print(f"Score: {score.value}")
```

### Running Your First Unit-Level Eval

```python
from ai_evolution import Experiment, HTTPAdapter, DeepDiffScorer, load_index_csv_dataset

# Load single test case
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    test_id="pipeline_create_001",
)

# Create adapter and scorer
adapter = HTTPAdapter(base_url="http://localhost:8000")
scorer = DeepDiffScorer(version="v3")

# Run experiment
experiment = Experiment(name="unit_test", dataset=dataset, scorers=[scorer])
result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")

# Check score
assert result.scores[0].value >= 0.9, f"Score {result.scores[0].value} below threshold"
```

## Core Concepts

### Test Case = DatasetItem

A test case is represented as a `DatasetItem`:

```python
from ai_evolution import DatasetItem

test_case = DatasetItem(
    id="test_001",                    # Unique test identifier
    input={"prompt": "..."},          # Input to your agent
    expected={"yaml": "..."},        # Expected output
    output=None,                      # Generated output (None until run)
    metadata={"entity_type": "pipeline"},  # Additional metadata
)
```

### Scorer = Evaluation Function

In ml-infra/evals, these are called "metrics". In ai-evolution, they're called "scorers":

```python
from ai_evolution import DeepDiffScorer

# DeepDiff v3 scorer (most common)
scorer = DeepDiffScorer(
    name="deep_diff_v3",
    eval_id="deep_diff_v3.v1",
    version="v3",
)
```

### Adapter = Connection to Your Agent

Adapters connect to your AI system/API:

```python
from ai_evolution import HTTPAdapter

adapter = HTTPAdapter(
    base_url="http://localhost:8000",
    auth_token="your-token",
    account_id="account-123",
    org_id="org-456",
    project_id="project-789",
)
```

### Experiment = Container for Test Cases + Scorers

An experiment groups test cases and scorers together:

```python
from ai_evolution import Experiment

experiment = Experiment(
    name="unit_test",
    dataset=[test_case],  # List of DatasetItem
    scorers=[scorer],      # List of Scorer
)
```

## Unit-Level Testing Patterns

### Pattern 1: Single Test Case

Test a single test case without running through an experiment:

```python
from ai_evolution import DatasetItem, DeepDiffScorer

# Create single test case
test_case = DatasetItem(
    id="pipeline_create_001",
    input={"prompt": "Create a pipeline..."},
    expected={"yaml": "pipeline:\n  name: test"},
)

# Score a single output
scorer = DeepDiffScorer(version="v3")
score = scorer.score(
    generated=generated_yaml,
    expected=test_case.expected,
    metadata={"test_id": test_case.id}
)

print(f"Score: {score.value}")
assert score.value >= 0.9, f"Score {score.value} below threshold"
```

### Pattern 2: Single Test Case with Adapter

Generate output and score it:

```python
from ai_evolution import DatasetItem, Experiment, DeepDiffScorer, HTTPAdapter

# Create single test case
test_case = DatasetItem(
    id="pipeline_create_001",
    input={"prompt": "Create a pipeline..."},
    expected={"yaml": "pipeline:\n  name: test"},
)

# Generate output and score
adapter = HTTPAdapter(base_url="http://localhost:8000")
scorer = DeepDiffScorer(version="v3")

experiment = Experiment(name="unit_test", dataset=[test_case], scorers=[scorer])
result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")

# Check result
assert result.scores[0].value >= 0.9
```

### Pattern 3: Filtered Test Suite (by test_id)

Load a specific test case from index CSV:

```python
from ai_evolution import load_index_csv_dataset, Experiment, DeepDiffScorer, HTTPAdapter

# Load specific test case
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    test_id="pipeline_create_001",  # Single test case
)

scorer = DeepDiffScorer(version="v3")
adapter = HTTPAdapter(base_url="http://localhost:8000")

experiment = Experiment(name="unit_test", dataset=dataset, scorers=[scorer])
result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
```

### Pattern 4: Small Test Suite (by entity/operation)

Load all tests for a specific entity type and operation:

```python
from ai_evolution import load_index_csv_dataset

# Load all pipeline create tests
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    entity_type="pipeline",
    operation_type="create",
)

# Run experiment with filtered dataset
experiment = Experiment(name="pipeline_create_tests", dataset=dataset, scorers=[scorer])
result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
```

### Pattern 5: pytest Integration

Use pytest for unit testing:

```python
import pytest
from ai_evolution import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset

@pytest.mark.asyncio
async def test_pipeline_create_001():
    """Test single pipeline creation case."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id="pipeline_create_001",
    )
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name="test_001", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Assert score meets threshold
    assert result.scores[0].value >= 0.9, f"Score {result.scores[0].value} below threshold"
```

### Pattern 6: pytest Parametrized Tests

Test multiple test cases:

```python
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
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name=f"test_{test_id}", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    assert result.scores[0].value >= 0.9
```

## Migration from ml-infra/evals

### Before (ml-infra/evals)

```bash
python3 benchmark_evals.py --use-index --test-id pipeline_create_001
```

### After (ai-evolution SDK)

```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval

result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    test_id="pipeline_create_001",
    model="claude-3-7-sonnet-20250219",
    output_csv="results/pipeline_create_001.csv",
)
```

### Using Convenience Functions

For even simpler unit testing:

```python
from ai_evolution.sdk.ml_infra import run_single_test

result = await run_single_test(
    test_id="pipeline_create_001",
    index_file="benchmarks/datasets/index.csv",
    adapter=adapter,
    scorer=DeepDiffScorer(version="v3"),
    model="claude-3-7-sonnet",
)
```

## Compatibility Verification

Verify that results match ml-infra/evals:

```python
from ai_evolution.sdk.ml_infra import compare_csv_results

comparison = compare_csv_results(
    csv1_path="ml-infra/evals/results.csv",
    csv2_path="ai-evolution/results.csv",
    tolerance=0.01,
)

assert comparison["differences"] == 0, "Results don't match!"
print(f"Matches: {comparison['matches']}")
print(f"Differences: {comparison['differences']}")
```

### Verify Single Test Compatibility

```python
from ai_evolution.sdk.ml_infra import verify_test_compatibility

is_compatible = await verify_test_compatibility(
    test_id="pipeline_create_001",
    tolerance=0.01,
)

assert is_compatible, "Test results don't match ml-infra/evals"
```

## Common Use Cases

### CI/CD Integration

Run pytest-based tests in CI/CD pipelines:

```python
# tests/test_pipeline_creation.py
import pytest
from ai_evolution import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset

@pytest.mark.asyncio
async def test_pipeline_creation_suite():
    """Run all pipeline creation tests."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        entity_type="pipeline",
        operation_type="create",
    )
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url=os.getenv("CHAT_BASE_URL"))
    
    experiment = Experiment(name="ci_pipeline_tests", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Assert all scores meet threshold
    for score in result.scores:
        assert score.value >= 0.9, f"Test {score.metadata.get('test_id')} failed"
```

### Local Development

Quick test of single test case during development:

```python
from ai_evolution.sdk.ml_infra import run_single_test, DeepDiffScorer, HTTPAdapter

# Quick test during development
result = await run_single_test(
    test_id="pipeline_create_001",
    index_file="benchmarks/datasets/index.csv",
    adapter=HTTPAdapter(base_url="http://localhost:8000"),
    scorer=DeepDiffScorer(version="v3"),
    model="claude-3-7-sonnet",
)

print(f"Score: {result.scores[0].value}")
```

### Regression Testing

Run all tests for specific entity type:

```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval

# Run all pipeline tests
result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    entity_type="pipeline",
    model="claude-3-7-sonnet",
    output_csv="results/pipeline_regression.csv",
)

# Check for regressions
for score in result.scores:
    if score.value < 0.9:
        print(f"Regression detected: {score.metadata.get('test_id')} = {score.value}")
```

### Threshold Testing

Pass/fail based on score threshold:

```python
@pytest.mark.asyncio
async def test_pipeline_create_threshold():
    """Test that pipeline creation meets quality threshold."""
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        test_id="pipeline_create_001",
    )
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name="threshold_test", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    # Threshold: 0.9 (90%)
    threshold = 0.9
    score_value = result.scores[0].value
    
    assert score_value >= threshold, (
        f"Score {score_value} below threshold {threshold} "
        f"for test {result.scores[0].metadata.get('test_id')}"
    )
```

### Offline Unit Testing

Test pre-generated outputs without API calls:

```python
from ai_evolution import load_index_csv_dataset, Experiment, DeepDiffScorer

# Load dataset with pre-generated outputs
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    offline=True,  # Enable offline mode
    actual_suffix="actual",  # Look for *_actual.yaml files
    test_id="pipeline_create_001",
)

# Score outputs directly (no adapter needed)
scorer = DeepDiffScorer(version="v3")
experiment = Experiment(name="offline_test", dataset=dataset, scorers=[scorer])

# Score items that have outputs
for item in dataset:
    if item.output:
        score = scorer.score(
            generated=item.output,
            expected=item.expected,
            metadata=item.metadata,
        )
        print(f"Test {item.id}: {score.value}")
```

## Using pytest Fixtures

Reusable fixtures for cleaner tests:

```python
# conftest.py or conftest_ml_infra.py
import pytest
import os
from ai_evolution import DeepDiffScorer, HTTPAdapter

@pytest.fixture
def ml_infra_adapter():
    """Fixture for ML Infra HTTP adapter."""
    return HTTPAdapter(
        base_url=os.getenv("CHAT_BASE_URL", "http://localhost:8000"),
        auth_token=os.getenv("CHAT_PLATFORM_AUTH_TOKEN", ""),
    )

@pytest.fixture
def deep_diff_scorer_v3():
    """Fixture for DeepDiff v3 scorer."""
    return DeepDiffScorer(version="v3")

@pytest.fixture
def test_dataset(test_id):
    """Fixture to load test dataset by test_id."""
    from ai_evolution import load_index_csv_dataset
    return load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        test_id=test_id,
    )
```

Then use in tests:

```python
@pytest.mark.asyncio
async def test_pipeline_create_001(ml_infra_adapter, deep_diff_scorer_v3, test_dataset):
    """Test using fixtures."""
    experiment = Experiment(
        name="test_001",
        dataset=test_dataset,
        scorers=[deep_diff_scorer_v3],
    )
    result = await experiment.run(
        adapter=ml_infra_adapter,
        model="claude-3-7-sonnet",
    )
    assert result.scores[0].value >= 0.9
```

## Best Practices

1. **Use test_id filtering** for single test cases during development
2. **Use pytest fixtures** for reusable setup
3. **Set score thresholds** for CI/CD pass/fail criteria
4. **Verify compatibility** with ml-infra/evals before migrating
5. **Use offline mode** for testing pre-generated outputs
6. **Group related tests** by entity_type and operation_type
7. **Assert on scores** to catch regressions early

## Troubleshooting

### Test Case Not Found

```python
# Ensure test_id exists in index.csv
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    test_id="pipeline_create_001",  # Verify this exists
)
assert len(dataset) > 0, "Test case not found"
```

### Score Mismatch with ml-infra/evals

```python
# Compare results
comparison = compare_csv_results(
    csv1_path="ml-infra/evals/results.csv",
    csv2_path="ai-evolution/results.csv",
    tolerance=0.01,
)

# Check specific test
if comparison["differences"] > 0:
    for diff in comparison["score_differences"]:
        print(f"Test {diff['test_id']}: {diff['csv1']} vs {diff['csv2']}")
```

### Adapter Connection Issues

```python
# Verify adapter configuration
adapter = HTTPAdapter(
    base_url="http://localhost:8000",  # Verify URL is correct
    auth_token="your-token",            # Verify token is valid
)

# Test connection
try:
    output = await adapter.generate({"prompt": "test"}, model="claude-3-7-sonnet")
except Exception as e:
    print(f"Adapter error: {e}")
```

## Next Steps

- See [ML Infra Onboarding Guide](ml-infra-onboarding.md) for full migration guide
- See [Migration Checklist](ml-infra-unit-testing-migration.md) for step-by-step migration
- See [SDK Documentation](sdk.md) for advanced features
- See `examples/ml_infra/unit_tests/` for complete examples
