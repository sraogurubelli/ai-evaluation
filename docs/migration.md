# Migration

Migrate from ml-infra/evals or MLInfraAdapter to AI Evaluation (aieval).

## Overview

- **Offline evals**: Use the DevOps consumer (`samples_sdk/consumers/devops`) for index-CSV + CSV output. Same workflow as ml-infra/evals.
- **Adapter**: `MLInfraAdapter` is removed. Use `HTTPAdapter` with your API config, or the DevOps consumer helpers.
- **Naming**: "metrics" in ml-infra → "scorers" in aieval (e.g. `DeepDiffScorer(version="v3")`).

## DevOps consumer (index-CSV + CSV)

Run from repo root with `PYTHONPATH=.` so `samples_sdk` is importable.

```python
from samples_sdk.consumers.devops import run_devops_eval, compare_csv_results

# Run eval (replaces benchmark_evals.py style)
result = await run_devops_eval(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    entity_type="pipeline",
    operation_type="create",
    model="claude-3-7-sonnet-20250219",
    output_csv="results/results.csv",
)

# Compare with previous run
comparison = compare_csv_results("old.csv", "new.csv", tolerance=0.01)
```

Unit tests: use `aieval.sdk.unit_test` (`run_single_item`, `score_single_output`, `assert_score_min`) or DevOps helpers. Fixtures: `tests/conftest_devops.py` (or `conftest_ml_infra.py` for `ml_infra_adapter` alias).

## CLI and config

- **CLI**: `aieval run --config config.yaml`. Config supports `type: "ml_infra"` for backward compat; under the hood it uses HTTPAdapter.
- **Config**: Same index CSV format. Set `adapter.type: "http"` and `base_url` / `auth_token` when moving off ml_infra.

## Custom adapter

If you need a team-specific API client: implement the `Adapter` interface or extend `HTTPAdapter`. See [custom-adapters.md](custom-adapters.md) and `examples/adapters/example_custom_adapter.py`.

## Dataset migration

To convert ml-infra/evals datasets to JSONL:

```bash
python migrations/ml_infra_evals/migration_script.py \
  --source-dir /path/to/ml-infra/evals/benchmarks/datasets \
  --output-dir ./datasets --entity-type pipeline
```

See [getting-started.md](getting-started.md) and [sdk-unit-testing.md](sdk-unit-testing.md) for full usage.
