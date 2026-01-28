# Metrics and Scorers

## Overview

In AI evaluation systems, **metrics** (also called **scorers**) are functions that measure the quality, correctness, or performance of AI-generated outputs. They are the core evaluation mechanism that produces scores for comparison and analysis.

## Terminology

### ml-infra/evals Terminology
- **Metrics**: Evaluation functions like `deep_diff_v1`, `deep_diff_v2`, `deep_diff_v3`
- Used in command-line: `--metrics deep_diff_v3 deep_diff_v2 deep_diff_v1`

### ai-evolution Terminology
- **Scorers**: Evaluation functions like `DeepDiffScorer` with `version="v1"`
- Used in API: `scorers_config: [{"type": "deep_diff", "version": "v3"}]`

**Key Point**: Metrics (ml-infra) = Scorers (ai-evolution) - they are the same concept with different naming.

## What Are Metrics/Scorers?

Metrics/Scorers are evaluation functions that:

1. **Take inputs**: Generated output, expected output, optional metadata
2. **Compute a score**: Numeric value (typically 0.0 to 1.0) or boolean
3. **Return results**: Score object with value, comment, and metadata

### Example: DeepDiff Scorer

```python
from ai_evolution.scorers.deep_diff import DeepDiffScorer

scorer = DeepDiffScorer(version="v3", entity_type="pipeline")

score = scorer.score(
    generated=yaml_output,
    expected=expected_yaml,
    metadata={"test_id": "pipeline_001"}
)

# score.value = 0.95 (similarity score)
# score.comment = "" (empty if perfect match)
# score.metadata = {"diff": "...", "test_id": "pipeline_001"}
```

## Architecture: Where Metrics/Scorers Belong

Metrics/Scorers are part of the evaluation pipeline at multiple levels:

### 1. API Layer (`src/ai_evolution/api/models.py`)

**Request Configuration**:
```python
class EvaluationRequest(BaseModel):
    scorers_config: list[dict[str, Any]]  # List of scorer configurations
    # Each config: {"type": "deep_diff", "version": "v3", ...}
```

**Response Results**:
```python
class EvaluationResponse(BaseModel):
    scores: list[dict[str, Any]]  # Scores from all scorers
    comparison: dict[str, Any]  # Model comparison (if multiple models)
```

### 2. Experiment Layer (`src/ai_evolution/core/experiment.py`)

**Experiment Definition**:
```python
experiment = Experiment(
    name="pipeline_benchmark",
    dataset=dataset_items,
    scorers=[scorer1, scorer2, scorer3]  # List of Scorer instances
)
```

### 3. Execution Layer (`src/ai_evolution/core/experiment.py::run()`)

**Evaluation Flow**:
```
For each dataset item:
  1. Generate output (via adapter)
  2. Apply all scorers to the output
  3. Collect scores from all scorers
  4. Store in ExperimentRun
```

### 4. Results Layer (`src/ai_evolution/core/types.py`)

**Score Storage**:
```python
@dataclass
class ExperimentRun:
    scores: list[Score]  # All scores from all scorers
    
@dataclass
class Score:
    name: str  # Scorer name (e.g., "deep_diff_v3")
    value: float  # Score value (0.0 to 1.0)
    eval_id: str  # Evaluation ID (e.g., "deep_diff_v3.v1")
    comment: str  # Optional comment/explanation
    metadata: dict[str, Any]  # Additional metadata
```

## Available Scorers

### DeepDiff Scorers

Compare YAML/JSON outputs using structural differences:

- **v1**: Basic DeepDiff comparison
- **v2**: DeepDiff with required field validation
- **v3**: DeepDiff with schema validation (most strict)

```python
{
  "type": "deep_diff",
  "version": "v3",  # or "v2" or "v1"
  "entity_type": "pipeline"  # Optional: pipeline, service, etc.
}
```

### Schema Validation Scorer

Validates output against a schema:

```python
{
  "type": "schema_validation",
  "validation_func": "path.to.validation.function"
}
```

### Dashboard Quality Scorer

Evaluates dashboard JSON quality:

```python
{
  "type": "dashboard_quality"
}
```

### Knowledge Graph Quality Scorer

Evaluates knowledge graph output quality:

```python
{
  "type": "kg_quality"
}
```

### LLM Judge Scorer

Uses an LLM to judge output quality:

```python
{
  "type": "llm_judge",
  "judge_model": "gpt-4o",
  "criteria": "Check if output is correct and complete"
}
```

### Autoevals-Style Scorers

From Braintrust/autoevals library:

- `factuality`: Factual correctness
- `helpfulness`: Helpfulness score
- `levenshtein`: String similarity
- `bleu`: BLEU score for text
- `embedding_similarity`: Semantic similarity
- `rag_relevance`: RAG relevance score

## Multiple Scorers

You can apply multiple scorers to the same output:

```json
{
  "scorers_config": [
    {"type": "deep_diff", "version": "v3"},
    {"type": "deep_diff", "version": "v2"},
    {"type": "deep_diff", "version": "v1"},
    {"type": "schema_validation"}
  ]
}
```

Each scorer produces a separate score, allowing you to:
- Compare different evaluation approaches
- Track improvements across scorer versions
- Combine multiple evaluation perspectives

## Multiple Models with Multiple Scorers

You can evaluate multiple models with the same set of scorers:

```json
{
  "models": ["claude-3-7-sonnet-20250219", "gpt-4o"],
  "scorers_config": [
    {"type": "deep_diff", "version": "v3"},
    {"type": "deep_diff", "version": "v2"}
  ]
}
```

This produces:
- One experiment run per model
- All scorers applied to each model's outputs
- Comparison scoreboard showing model performance per scorer

## Mapping: ml-infra → ai-evolution

### ml-infra Command
```bash
python3 benchmark_evals.py \
  --metrics deep_diff_v3 deep_diff_v2 deep_diff_v1 \
  --models claude-3-7-sonnet-20250219 gpt-4o
```

### ai-evolution API Equivalent
```json
{
  "experiment_name": "pipeline_benchmark",
  "scorers_config": [
    {"type": "deep_diff", "version": "v3"},
    {"type": "deep_diff", "version": "v2"},
    {"type": "deep_diff", "version": "v1"}
  ],
  "models": ["claude-3-7-sonnet-20250219", "gpt-4o"],
  "dataset_config": {...},
  "adapter_config": {...}
}
```

## Creating Custom Scorers

To create a custom scorer, implement the `Scorer` base class:

```python
from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score

class CustomScorer(Scorer):
    def __init__(self, name: str = "custom", eval_id: str = "custom.v1"):
        super().__init__(name, eval_id)
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        # Your evaluation logic here
        score_value = compute_score(generated, expected)
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment="Custom evaluation",
            metadata=metadata,
        )
```

## Best Practices

1. **Use Multiple Scorers**: Combine different evaluation approaches for comprehensive assessment
2. **Version Your Scorers**: Use versioned scorer names (e.g., `deep_diff_v3`) for tracking improvements
3. **Include Metadata**: Add context to scores via metadata (test_id, entity_type, etc.)
4. **Handle Edge Cases**: Return appropriate scores for None/empty/invalid inputs
5. **Document Scorer Behavior**: Clearly document what each scorer measures and how scores are computed

## Summary

- **Metrics** (ml-infra) = **Scorers** (ai-evolution)
- Scorers are evaluation functions that measure output quality
- Multiple scorers can be applied to the same output
- Multiple models can be evaluated with the same scorers
- Scorers belong at API, Experiment, Execution, and Results layers
- Custom scorers can be created by implementing the `Scorer` base class
