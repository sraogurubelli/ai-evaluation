# Unit Testing Examples

This directory contains examples for unit-level evaluation testing with ai-evolution SDK.

## Files

- **`test_single_case.py`**: Examples for testing a single test case
- **`test_pytest_integration.py`**: Examples for pytest-based unit tests (CI/CD integration)
- **`test_small_suite.py`**: Examples for running small test suites (entity/operation filtering)
- **`test_threshold.py`**: Examples for threshold-based pass/fail testing
- **`test_offline_unit.py`**: Examples for offline unit testing (pre-generated outputs)

## Usage

### Running Examples

```bash
# Run a single example
python examples/ml_infra/unit_tests/test_single_case.py

# Run pytest examples
pytest examples/ml_infra/unit_tests/test_pytest_integration.py -v
```

### Prerequisites

1. **Dataset**: Ensure you have `benchmarks/datasets/index.csv` and corresponding test files
2. **API Server**: For examples that use adapters, ensure your ML Infra API server is running
3. **Environment Variables**: Set required environment variables:
   ```bash
   export CHAT_BASE_URL="http://localhost:8000"
   export CHAT_PLATFORM_AUTH_TOKEN="your-token"
   ```

### Example: Single Test Case

```python
from ai_evolution import DatasetItem, DeepDiffScorer

test_case = DatasetItem(
    id="pipeline_create_001",
    input={"prompt": "Create a pipeline..."},
    expected={"yaml": "pipeline:\n  name: test"},
)

scorer = DeepDiffScorer(version="v3")
score = scorer.score(
    generated=generated_yaml,
    expected=test_case.expected,
    metadata={"test_id": test_case.id}
)
```

### Example: pytest Integration

```python
import pytest
from ai_evolution import Experiment, DeepDiffScorer, HTTPAdapter, load_index_csv_dataset

@pytest.mark.asyncio
async def test_pipeline_create_001():
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        test_id="pipeline_create_001",
    )
    
    scorer = DeepDiffScorer(version="v3")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(name="test_001", dataset=dataset, scorers=[scorer])
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet")
    
    assert result.scores[0].value >= 0.9
```

## See Also

- [SDK Unit Testing Guide](../../../docs/sdk-unit-testing.md) - Comprehensive guide for unit-level testing
- [ML Infra Onboarding Guide](../../../docs/ml-infra-onboarding.md) - Migration guide from ml-infra/evals
- [Migration Checklist](../../../docs/ml-infra-unit-testing-migration.md) - Step-by-step migration checklist
