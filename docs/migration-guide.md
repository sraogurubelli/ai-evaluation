# Migration Guide: ml-infra/evals → AI Evolution

## Overview

This guide helps you migrate from `ml-infra/evals` to AI Evolution.

**Note**: The ml-infra adapter in AI Evolution is designed to work with ml-infra server APIs. If you're using a different AI system, you can create a custom adapter following the `Adapter` interface.

## Migration Strategy

### Phase 1: Parallel Running (Weeks 1-4)

Run both systems in parallel to validate:

1. Install new platform alongside ml-infra/evals
2. Run same experiments on both systems
3. Compare results
4. Identify any discrepancies

### Phase 2: Gradual Migration (Weeks 5-8)

Migrate one entity type at a time:

1. Start with pipelines (most common)
2. Update CI/CD to use new platform
3. Keep ml-infra/evals as fallback
4. Migrate other entity types incrementally

### Phase 3: Full Migration (Weeks 9-12)

Complete migration:

1. All evaluations use new platform
2. ml-infra/evals marked as deprecated
3. Documentation updated
4. Old system removed

## Step-by-Step Migration

### 1. Migrate Datasets

```bash
# Run migration script
python migrations/ml_infra_evals/migration_script.py \
  --source-dir ../ml-infra/evals/benchmarks/datasets \
  --output-dir examples/ml_infra/datasets \
  --entity-type pipeline
```

This creates:
- JSONL dataset file
- Preserved file structure
- Metadata preserved

### 2. Create Config File

Create `config.yaml` based on your ml-infra/evals usage:

```yaml
experiment:
  name: "pipeline_creation_benchmark"

dataset:
  type: "index_csv"
  index_file: "../ml-infra/evals/benchmarks/datasets/index.csv"
  base_dir: "../ml-infra/evals/benchmarks/datasets"
  filters:
    entity_type: "pipeline"
    operation_type: "create"

adapter:
  type: "ml_infra"
  base_url: "${CHAT_BASE_URL}"
  auth_token: "${CHAT_PLATFORM_AUTH_TOKEN}"

models:
  - "claude-3-7-sonnet-20250219"

scorers:
  - type: "deep_diff"
    version: "v3"
  - type: "deep_diff"
    version: "v2"

execution:
  concurrency_limit: 5

output:
  sinks:
    - type: "csv"
      path: "results/results.csv"
```

### 3. Run Experiment

```bash
ai-evolution run --config config.yaml
```

### 4. Compare Results

Compare CSV outputs:
- Old: `ml-infra/evals/benchmarks/model_results/*.csv`
- New: `results/results.csv`

### 5. Update CI/CD

Replace ml-infra/evals commands:

**Old:**
```bash
python3 benchmark_evals.py --use-index --entity-type pipeline
```

**New:**
```bash
ai-evolution run --config config.yaml
```

## Key Differences

### Dataset Format

**Old (ml-infra/evals):**
- Index CSV + separate files
- Loaded via `load_data_from_index()`

**New:**
- Same format supported via `index_csv` loader
- Also supports JSONL and function-based

### Scoring

**Old:**
- Hardcoded metrics in `add_metric()`
- DeepDiff v1/v2/v3

**New:**
- Scorer abstraction
- Same DeepDiff scorers, but extensible

### Output

**Old:**
- CSV files only
- No trace linking

**New:**
- Multiple sinks (CSV, JSON, Langfuse, stdout)
- Optional Langfuse integration for trace linking

## Validation Checklist

- [ ] Datasets load correctly
- [ ] Results match ml-infra/evals (within tolerance)
- [ ] All entity types work
- [ ] CI/CD integration works
- [ ] Langfuse integration works (if used)
- [ ] Documentation updated

## Troubleshooting

### Results Don't Match

- Check scorer versions match
- Verify entity type detection
- Check YAML parsing differences

### Missing Scores

- Verify scorer configuration
- Check for errors in scorer execution
- Review metadata for entity type

### Performance Issues

- Adjust `concurrency_limit`
- Check ml-infra server capacity
- Review network latency

## Support

For issues during migration:
1. Check logs for errors
2. Compare with ml-infra/evals outputs
3. Review example configs
4. Open issue with details
