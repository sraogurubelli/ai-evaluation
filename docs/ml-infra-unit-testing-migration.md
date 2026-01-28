# ML Infra Unit Testing Migration Checklist

This checklist helps ML Infra agent dev teams migrate their unit-level evaluation tests from `ml-infra/evals` to `ai-evolution` SDK.

## Pre-Migration

- [ ] **Review existing tests**: Identify all unit-level evaluation tests in your codebase
- [ ] **Document test patterns**: Note how tests are currently structured (single cases, suites, pytest, etc.)
- [ ] **Identify test locations**: Map where test cases are stored (index.csv, test files, etc.)
- [ ] **Review dependencies**: Check what ml-infra/evals features you're using

## Installation & Setup

- [ ] **Install ai-evolution**: `pip install ai-evolution` or `pip install -e .` for development
- [ ] **Verify installation**: Run `python -c "import ai_evolution; print(ai_evolution.__version__)"`
- [ ] **Set environment variables**: Configure `CHAT_BASE_URL`, `CHAT_PLATFORM_AUTH_TOKEN`, etc.
- [ ] **Verify dataset access**: Ensure you can access `benchmarks/datasets/index.csv` and test files

## Migration Steps

### Step 1: Identify Existing Unit-Level Tests

- [ ] **List all test cases**: Document all test_ids you're currently testing
- [ ] **Group by entity type**: Categorize tests by entity_type (pipeline, service, dashboard, etc.)
- [ ] **Group by operation**: Categorize tests by operation_type (create, update, insights)
- [ ] **Note test patterns**: Document how tests are run (single cases, suites, pytest, etc.)

### Step 2: Map ml-infra Patterns to ai-evolution SDK

- [ ] **Map test loading**: Replace `--test-id` with `load_index_csv_dataset(test_id=...)`
- [ ] **Map metrics to scorers**: Replace `--metrics deep_diff_v3` with `DeepDiffScorer(version="v3")`
- [ ] **Map adapter config**: Replace ml-infra adapter with `HTTPAdapter(base_url=..., auth_token=...)`
- [ ] **Map experiment execution**: Replace `benchmark_evals.py` with `Experiment.run()` or `run_ml_infra_eval()`

### Step 3: Create Adapter for Your Agent

- [ ] **Review HTTPAdapter**: Check if generic `HTTPAdapter` works for your API
- [ ] **Configure adapter**: Set `base_url`, `auth_token`, `account_id`, `org_id`, `project_id`
- [ ] **Test adapter**: Verify adapter can generate outputs from your API
- [ ] **Create custom adapter** (if needed): Extend `HTTPAdapter` or create new adapter class

### Step 4: Convert Test Cases to DatasetItem Format

- [ ] **Verify dataset format**: Ensure your index.csv matches expected format
- [ ] **Test dataset loading**: Run `load_index_csv_dataset()` on your dataset
- [ ] **Verify test_id filtering**: Test loading single test case by test_id
- [ ] **Verify entity/operation filtering**: Test filtering by entity_type and operation_type

### Step 5: Replace Metric Calls with Scorer Instances

- [ ] **Map DeepDiff versions**: Replace `deep_diff_v1/v2/v3` with `DeepDiffScorer(version="v1/v2/v3")`
- [ ] **Create scorer instances**: Create scorer objects for each metric you use
- [ ] **Test scorer scoring**: Verify scorers produce same scores as ml-infra/evals
- [ ] **Handle custom metrics**: Create custom scorers if you have domain-specific metrics

### Step 6: Verify Results Match ml-infra/evals Output

- [ ] **Run same test cases**: Run identical test cases through both systems
- [ ] **Compare CSV outputs**: Use `compare_csv_results()` to compare results
- [ ] **Check score differences**: Verify scores match within tolerance (default: 0.01)
- [ ] **Investigate discrepancies**: Document and resolve any score differences
- [ ] **Verify metadata**: Ensure test_id, entity_type, etc. are preserved

### Step 7: Integrate into pytest/CI/CD

- [ ] **Create pytest fixtures**: Use `conftest_ml_infra.py` fixtures or create your own
- [ ] **Convert to pytest tests**: Convert existing test scripts to pytest format
- [ ] **Add assertions**: Add score threshold assertions for pass/fail
- [ ] **Test CI/CD integration**: Verify tests run correctly in CI/CD pipeline
- [ ] **Set exit codes**: Ensure tests exit with appropriate codes for CI/CD

## Post-Migration

- [ ] **Run full test suite**: Execute all migrated tests
- [ ] **Compare with baseline**: Verify all results match ml-infra/evals baseline
- [ ] **Update documentation**: Update team documentation with new patterns
- [ ] **Train team members**: Share migration guide and examples with team
- [ ] **Monitor for regressions**: Set up regression testing with thresholds

## Verification Checklist

- [ ] **Single test cases work**: Can test individual test cases by test_id
- [ ] **Test suites work**: Can test filtered suites (entity_type, operation_type)
- [ ] **pytest integration works**: Tests run successfully with pytest
- [ ] **CI/CD integration works**: Tests pass/fail correctly in CI/CD
- [ ] **Results match**: Scores match ml-infra/evals output exactly
- [ ] **Offline mode works**: Can test pre-generated outputs without API calls
- [ ] **Threshold testing works**: Pass/fail based on score thresholds

## Common Patterns

### Pattern 1: Single Test Case

**Before (ml-infra/evals)**:
```bash
python3 benchmark_evals.py --use-index --test-id pipeline_create_001
```

**After (ai-evolution)**:
```python
from ai_evolution.sdk.ml_infra import run_single_test, DeepDiffScorer, HTTPAdapter

result = await run_single_test(
    test_id="pipeline_create_001",
    index_file="benchmarks/datasets/index.csv",
    adapter=HTTPAdapter(base_url="http://localhost:8000"),
    scorer=DeepDiffScorer(version="v3"),
    model="claude-3-7-sonnet",
)
```

### Pattern 2: Test Suite

**Before (ml-infra/evals)**:
```bash
python3 benchmark_evals.py --use-index --entity-type pipeline --operation-type create
```

**After (ai-evolution)**:
```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval

result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    entity_type="pipeline",
    operation_type="create",
    model="claude-3-7-sonnet",
)
```

### Pattern 3: pytest Integration

**Before (ml-infra/evals)**:
```bash
# Custom test script
python3 test_pipeline_create.py
```

**After (ai-evolution)**:
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

## Troubleshooting

### Test Case Not Found

- [ ] **Verify test_id exists**: Check index.csv for test_id
- [ ] **Check file paths**: Verify index_file and base_dir paths are correct
- [ ] **Check filtering**: Ensure entity_type/operation_type filters aren't excluding test case

### Score Mismatch

- [ ] **Compare scorer versions**: Ensure using same DeepDiff version (v1/v2/v3)
- [ ] **Check YAML parsing**: Verify YAML parsing matches ml-infra/evals
- [ ] **Compare individual scores**: Use `compare_csv_results()` to find differences
- [ ] **Check metadata**: Ensure entity_type, test_id are correct

### Adapter Issues

- [ ] **Verify API URL**: Check base_url is correct
- [ ] **Check authentication**: Verify auth_token is valid
- [ ] **Test connection**: Try generating output manually with adapter
- [ ] **Check error messages**: Review adapter error logs

### pytest Issues

- [ ] **Install pytest-asyncio**: Ensure `pytest-asyncio` is installed
- [ ] **Use @pytest.mark.asyncio**: Mark async test functions
- [ ] **Check fixtures**: Verify fixtures are loaded correctly
- [ ] **Check imports**: Ensure all imports are correct

## Resources

- [Unit Testing Guide](sdk-unit-testing.md) - Comprehensive unit testing guide
- [ML Infra Onboarding Guide](ml-infra-onboarding.md) - Full migration guide
- [SDK Documentation](sdk.md) - SDK reference
- `examples/ml_infra/unit_tests/` - Example test files
- `tests/conftest_ml_infra.py` - pytest fixtures

## Support

If you encounter issues during migration:

1. Check the [Unit Testing Guide](sdk-unit-testing.md) for examples
2. Review `examples/ml_infra/unit_tests/` for working examples
3. Compare your code with example patterns
4. Use `compare_csv_results()` to verify compatibility
5. Open an issue with details about your specific use case
