"""DevOps consumer SDK – helpers for DevOps/Harness evaluation workflow.

Use these after installing ai-evolution and adding the repo root to PYTHONPATH
so that 'samples_sdk' is importable, or copy this module into your project.

Framework-agnostic helpers (score_single_output, run_single_item) live in
aieval.sdk.unit_test.
"""

from samples_sdk.consumers.devops.devops import (
    create_devops_experiment,
    run_devops_eval,
    compare_csv_results,
    create_devops_sinks,
    load_single_test_case,
    score_single_output,
    run_single_test,
    verify_test_compatibility,
)

__all__ = [
    "create_devops_experiment",
    "run_devops_eval",
    "compare_csv_results",
    "create_devops_sinks",
    "load_single_test_case",
    "score_single_output",
    "run_single_test",
    "verify_test_compatibility",
]
