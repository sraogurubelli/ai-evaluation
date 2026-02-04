# Metrics and Scorers

Scorers evaluate AI outputs and produce scores (e.g. 0.0–1.0).

## Terminology

- **ml-infra/evals:** "metrics" (e.g. `deep_diff_v3`).
- **aieval:** "scorers" (e.g. `DeepDiffScorer(version="v3")`). Same concept.

## Built-in scorers

- **DeepDiff** (v1, v2, v3): Compare YAML/JSON; v3 strictest.
- **Schema validation:** Validate output against schema.
- **LLM-as-judge:** Rubric-based evaluation (optional `.[llm]`).
- **Entity-specific:** Dashboard quality, KG quality.

## Usage

```python
from aieval import DeepDiffScorer

scorer = DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")
score = scorer.score(generated=yaml_out, expected=expected_yaml, metadata={})
# score.value, score.comment, score.metadata
```

Use in `Experiment(scorers=[...])` or SDK runner. Custom scorers: implement `Scorer` interface (see `aieval.scorers.base`).
