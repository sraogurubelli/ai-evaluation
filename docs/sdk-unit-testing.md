# SDK Unit Testing

Unit-level evaluation tests with aieval.

## Quick start

**Single test case (framework):**

```python
from aieval import run_single_item, assert_score_min, DeepDiffScorer, HTTPAdapter

result = await run_single_item(
    dataset_item=test_case,
    adapter=HTTPAdapter(base_url="http://localhost:8000"),
    scorer=DeepDiffScorer(version="v3"),
    model="claude-3-7-sonnet",
)
assert_score_min(result, min_value=0.9)
```

**Index CSV + CSV output (DevOps consumer):** Use `samples_sdk/consumers/devops` (run from repo root with `PYTHONPATH=.`). See [migration](migration.md).

## Concepts

- **Test case** = `DatasetItem(id, input, expected, metadata)`.
- **Scorer** = e.g. `DeepDiffScorer(version="v3")`. Same as "metrics" in ml-infra.
- **Adapter** = `HTTPAdapter(base_url, auth_token, ...)` or custom. See [custom-adapters](custom-adapters.md).

## Helpers (aieval.sdk.unit_test)

- `run_single_item(dataset_item, adapter, scorer, model)` — run one item, return result with scores.
- `score_single_output(scorer, generated, expected, metadata)` — score only (no API call).
- `assert_score_min(result, min_value=..., score_name=...)` — assert min score or fail.

## pytest

Use `tests/conftest_devops.py` (or `conftest_ml_infra.py`) for fixtures. Example:

```python
@pytest.mark.asyncio
async def test_pipeline_create(devops_adapter):
    dataset = load_index_csv_dataset(..., test_id="pipeline_create_001")
    experiment = Experiment(name="test", dataset=dataset, scorers=[DeepDiffScorer(version="v3")])
    result = await experiment.run(adapter=devops_adapter, model="claude-3-7-sonnet")
    assert result.scores[0].value >= 0.9
```

## Next steps

- [Migration](migration.md) for ml-infra/evals migration
- [SDK](sdk.md) for advanced features
- `examples/ml_infra/unit_tests/` for full examples
