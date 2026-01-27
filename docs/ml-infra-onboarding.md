# ML Infra Onboarding Guide

This guide helps ML Infra teams migrate from `ml-infra/evals` to AI Evolution SDK for offline evaluations.

## Overview

AI Evolution provides a unified evaluation platform that supports ML Infra's existing workflow while offering additional capabilities like experiment tracking, comparison, and extensibility.

## Quick Start

### Installation

```bash
# Install AI Evolution
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

### Basic Usage

**Old (ml-infra/evals):**
```bash
python3 benchmark_evals.py --use-index --entity-type pipeline --operation-type create
```

**New (AI Evolution SDK):**
```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval

result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    entity_type="pipeline",
    operation_type="create",
    model="claude-3-7-sonnet-20250219",
    output_csv="results/pipeline_create.csv",
)
```

## Migration Path

### Phase 1: Parallel Running (Validation)

Run both systems in parallel to validate compatibility:

1. **Install AI Evolution** alongside ml-infra/evals
2. **Run same dataset** through both systems
3. **Compare outputs** using `compare_csv_results()`
4. **Identify discrepancies** and validate they're acceptable

```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval, compare_csv_results

# Run with AI Evolution
result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    entity_type="pipeline",
    output_csv="results/ai_evolution.csv",
)

# Compare with ml-infra/evals output
comparison = compare_csv_results(
    csv1_path="ml-infra/evals/results.csv",
    csv2_path="results/ai_evolution.csv",
    tolerance=0.01,
)

print(f"Matches: {comparison['matches']}")
print(f"Differences: {comparison['differences']}")
```

### Phase 2: Gradual Migration

Migrate one entity type at a time:

1. **Start with pipelines** (most common)
2. **Update CI/CD** to use AI Evolution
3. **Keep ml-infra/evals** as fallback
4. **Migrate other entity types** incrementally

### Phase 3: Full Migration

Complete migration:

1. All evaluations use AI Evolution
2. ml-infra/evals marked as deprecated
3. Documentation updated
4. Old system removed

## Key Concepts

### Dataset Format

AI Evolution supports the exact same index CSV format as ml-infra/evals:

```csv
test_id,entity_type,operation_type,prompt_file,old_yaml_file,expected_yaml_file,notes,tags
pipeline_create_001,pipeline,create,pipelines/create/001_prompt.txt,,pipelines/create/001_expected.yaml,...
```

No changes needed to your existing datasets!

### Scorers

AI Evolution provides the same DeepDiff scorers:

- `deep_diff_v1`: Basic DeepDiff
- `deep_diff_v2`: DeepDiff + required field validation
- `deep_diff_v3`: DeepDiff + schema validation

Results should match ml-infra/evals exactly.

### Offline Mode

AI Evolution supports offline evaluation (benchmarking pre-generated outputs):

```python
from ai_evolution import load_index_csv_dataset

# Load dataset in offline mode
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    base_dir="benchmarks/datasets",
    entity_type="pipeline",
    offline=True,  # Enable offline mode
    actual_suffix="actual",  # Look for *_actual.yaml files
)
```

### Output Format

CSV output format matches ml-infra/evals structure:

- All score fields as columns
- Metadata flattened into columns
- Compatible with existing analysis tools

## Common Patterns

### Pattern 1: Single Model Evaluation

```python
from ai_evolution.sdk.ml_infra import run_ml_infra_eval

result = await run_ml_infra_eval(
    index_file="benchmarks/datasets/index.csv",
    entity_type="pipeline",
    model="claude-3-7-sonnet-20250219",
    output_csv="results/pipeline.csv",
)
```

### Pattern 2: Multi-Model Comparison

```python
models = ["claude-3-7-sonnet-20250219", "gpt-4o"]
runs = []

for model in models:
    result = await run_ml_infra_eval(
        index_file="benchmarks/datasets/index.csv",
        entity_type="pipeline",
        model=model,
        output_csv=f"results/pipeline_{model}.csv",
    )
    runs.append(result)

# Compare models
from ai_evolution import compare_runs
comparison = compare_runs(runs[0], runs[1])
```

### Pattern 3: Offline Evaluation

```python
from ai_evolution import Experiment, DeepDiffScorer, load_index_csv_dataset, CSVSink

# Load dataset with pre-generated outputs
dataset = load_index_csv_dataset(
    index_file="benchmarks/datasets/index.csv",
    offline=True,
    actual_suffix="generated",
)

# Score outputs
scorers = [DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3")]
experiment = Experiment(name="offline_eval", dataset=dataset, scorers=scorers)

# Score directly (no adapter needed)
all_scores = []
for item in dataset:
    if item.output:
        for scorer in scorers:
            score = scorer.score(item.output, item.expected, item.metadata)
            all_scores.append(score)

# Save results
csv_sink = CSVSink("results/offline.csv")
# ... emit scores
```

### Pattern 4: Entity-Specific Evaluation

```python
# Pipeline evaluation
pipeline_experiment = create_ml_infra_experiment(
    index_file="benchmarks/datasets/index.csv",
    entity_type="pipeline",
    operation_type="create",
)

# Dashboard evaluation
from ai_evolution import DashboardQualityScorer
dashboard_experiment = Experiment(
    name="dashboard_eval",
    dataset=load_index_csv_dataset(..., entity_type="dashboard"),
    scorers=[DashboardQualityScorer()],
)
```

## Configuration

### Environment Variables

Set these environment variables (same as ml-infra/evals):

```bash
export CHAT_BASE_URL="http://localhost:8000"
export CHAT_PLATFORM_AUTH_TOKEN="your-token"
export ACCOUNT_ID="account-123"
export ORG_ID="org-456"
export PROJECT_ID="project-789"
```

### Config File

You can also use YAML config files:

```yaml
experiment:
  name: "pipeline_creation_benchmark"

dataset:
  type: "index_csv"
  index_file: "benchmarks/datasets/index.csv"
  base_dir: "benchmarks/datasets"
  filters:
    entity_type: "pipeline"
    operation_type: "create"
  offline: false

adapter:
  type: "ml_infra"
  base_url: "${CHAT_BASE_URL}"
  auth_token: "${CHAT_PLATFORM_AUTH_TOKEN}"

scorers:
  - type: "deep_diff"
    version: "v3"
  - type: "deep_diff"
    version: "v2"

output:
  sinks:
    - type: "csv"
      path: "results/results.csv"
```

Then run:
```bash
ai-evolution run --config config.yaml
```

## Validation Checklist

Before migrating, verify:

- [ ] Datasets load correctly
- [ ] Results match ml-infra/evals (within tolerance)
- [ ] All entity types work (pipeline, service, dashboard, KG)
- [ ] Offline mode works
- [ ] Update operations work (old_yaml handling)
- [ ] CSV output format matches
- [ ] CI/CD integration works

## Troubleshooting

### Results Don't Match

1. **Check scorer versions**: Ensure using same DeepDiff versions
2. **Verify entity type detection**: Check metadata for correct entity_type
3. **Check YAML parsing**: Ensure YAML parsing matches ml-infra/evals
4. **Compare individual scores**: Use `compare_csv_results()` to find differences

### Missing Scores

1. **Check scorer configuration**: Verify scorers are created correctly
2. **Check for errors**: Review logs for scorer execution errors
3. **Verify metadata**: Ensure entity_type is in metadata

### Performance Issues

1. **Adjust concurrency**: Reduce `concurrency_limit` if server overloaded
2. **Check network latency**: Review API call timing
3. **Monitor server capacity**: Ensure ml-infra server can handle load

## Examples

See `examples/ml_infra/` for complete examples:

- `sdk_offline_eval.py`: Offline evaluation workflow
- `sdk_multi_model.py`: Multi-model comparison
- `sdk_entity_specific.py`: Entity-specific patterns
- `migration_example.py`: Before/after migration comparison

## Support

For issues during migration:

1. Check logs for errors
2. Compare with ml-infra/evals outputs
3. Review example configs
4. Open issue with details

## Next Steps

After successful migration:

1. Explore additional features (experiment comparison, Langfuse integration)
2. Add custom scorers for domain-specific metrics
3. Integrate with Admin UI for visualization (future)
4. Contribute improvements back to the platform
