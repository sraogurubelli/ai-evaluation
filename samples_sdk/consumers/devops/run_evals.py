#!/usr/bin/env python3
"""Example script: run DevOps evals using the consumer SDK.

Run from ai-evaluation repo root with PYTHONPATH=. so samples_sdk is importable:

    PYTHONPATH=. python samples_sdk/consumers/devops/run_evals.py

Or from this directory:

    PYTHONPATH=/path/to/ai-evaluation python run_evals.py
"""

import asyncio
import sys
from pathlib import Path

# Ensure repo root (or ai-evaluation) is on path so samples_sdk is importable
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from samples_sdk.consumers.devops import (
    create_devops_experiment,
    run_devops_eval,
    create_devops_sinks,
)


async def main():
    """Run a small DevOps eval (example)."""
    index_file = Path("benchmarks/datasets/index.csv")
    if not index_file.exists():
        print("Create benchmarks/datasets/index.csv and add test cases, then re-run.")
        return

    print("Creating DevOps experiment...")
    experiment = create_devops_experiment(
        index_file=str(index_file),
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    print(f"  Dataset size: {len(experiment.dataset)}")
    print(f"  Scorers: {[s.name for s in experiment.scorers]}")

    # Run eval only when not offline (adapter is required for experiment.run)
    offline = True  # Set False when you have a live server at base_url
    if offline:
        print("\nSkipping run (offline=True). Set offline=False and ensure server is up to run eval.")
    else:
        print("\nRunning eval...")
        result = await run_devops_eval(
            index_file=str(index_file),
            base_dir="benchmarks/datasets",
            entity_type="pipeline",
            operation_type="create",
            model="claude-3-7-sonnet",
            base_url="http://localhost:8000",
            offline=False,
            output_csv=None,
            concurrency_limit=2,
        )
        print(f"  Run id: {result.run_id}")
        print(f"  Scores: {[(s.name, s.value) for s in result.scores]}")


if __name__ == "__main__":
    asyncio.run(main())
