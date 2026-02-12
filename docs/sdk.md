# SDK

Run evals programmatically with the aieval SDK. Define an **Eval** (name, data set, scorers), run it, and get a **Run** with **Scores**. In the SDK, an Eval is represented by the `Experiment` class.

## Quick start

```python
from aieval import Experiment, HTTPAdapter, DeepDiffScorer, load_jsonl_dataset

dataset = load_jsonl_dataset("dataset.jsonl")
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="your-token")
scorers = [DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")]

experiment = Experiment(name="my_eval", dataset=dataset, scorers=scorers)
result = await experiment.run(adapter=adapter, model="gpt-4o")
```

The `result` is a Run (scores and metadata). See [Concepts](concepts.md) for Eval, Run, Data Set, Task, Trace, Scores.

## Core types

- **Dataset:** `load_jsonl_dataset(path)` or index CSV via `samples_sdk/consumers/devops`. Items are `DatasetItem(id, input, expected)`.
- **Adapter:** `HTTPAdapter(base_url, auth_token, ...)` for any REST API. See [custom-adapters](custom-adapters.md).
- **Scorers:** `DeepDiffScorer(version="v1"|"v2"|"v3")`, schema validation, LLM judge. See [metrics-and-scorers](metrics-and-scorers.md).
- **Sinks:** `CSVSink(path)`, `StdoutSink()`, `JSONSink(path)`.

## Unit testing

Use `run_single_item`, `score_single_output`, `assert_score_min` from `aieval.sdk.unit_test`. For index-CSV + CSV: `samples_sdk/consumers/devops`. See [sdk-unit-testing.md](sdk-unit-testing.md).

## More

- **Runner:** `EvaluationRunner` for ai-evals-style flows (see package `aieval.sdk.runner`).
- **Registry:** `run_from_registry` for registry-based evals.
- **Comparison:** `compare_runs`, `get_regressions` from `aieval.sdk.comparison`.
