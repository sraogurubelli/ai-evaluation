# ML Infra Evals Migration Guide

This directory contains tools and scripts for migrating from `ml-infra/evals` to the new AI Evolution Platform.

## Migration Process

1. **Run Migration Script**: Converts existing datasets to new format
2. **Validate**: Ensure all datasets load correctly
3. **Test**: Run experiments and compare results
4. **Gradual Migration**: Migrate one entity type at a time

## Usage

```bash
# Migrate all datasets
python migrations/ml_infra_evals/migration_script.py \
  --source-dir ../ml-infra/evals/benchmarks/datasets \
  --output-dir examples/ml_infra/datasets

# Migrate specific entity type
python migrations/ml_infra_evals/migration_script.py \
  --source-dir ../ml-infra/evals/benchmarks/datasets \
  --output-dir examples/ml_infra/datasets \
  --entity-type pipeline
```

## What Gets Migrated

- Index CSV structure → New dataset format
- Test cases → Dataset items
- Expected outputs → Preserved
- Metadata → Preserved in dataset items

## Validation

After migration, validate by:
1. Loading datasets with new platform
2. Running experiments
3. Comparing results with original ml-infra/evals outputs

### Validation Script

Use the `validate_migration.py` script to compare CSV outputs from both systems:

```bash
# Basic comparison
python migrations/ml_infra_evals/validate_migration.py \
  --old-csv ml-infra/evals/results.csv \
  --new-csv ai-evolution/results.csv

# With custom tolerance and detailed report
python migrations/ml_infra_evals/validate_migration.py \
  --old-csv ml-infra/evals/results.csv \
  --new-csv ai-evolution/results.csv \
  --tolerance 0.001 \
  --output-report validation_report.json \
  --verbose
```

The validation script will:
- Compare row counts and test IDs
- Check for missing columns
- Compare scores with configurable tolerance
- Report differences grouped by test ID
- Generate a pass/fail status (passes if 95%+ match)
- Optionally save a detailed JSON report

**Exit codes:**
- `0`: Validation passed
- `1`: Validation failed or errors occurred
