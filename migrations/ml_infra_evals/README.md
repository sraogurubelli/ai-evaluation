# ML Infra evals migration

Convert ml-infra/evals datasets to the new format. Run: `python migrations/ml_infra_evals/migration_script.py --source-dir <path> --output-dir <path> [--entity-type pipeline]`. Validate: `validate_migration.py --old-csv <old> --new-csv <new>`. See [docs/migration.md](../../docs/migration.md).
