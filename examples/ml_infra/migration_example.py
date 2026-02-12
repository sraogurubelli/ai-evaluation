"""Example: Migration from ml-infra/evals to AI Evolution SDK.

This shows a before/after comparison of migrating from ml-infra/evals to AI Evolution.
"""

# ============================================================================
# BEFORE: ml-infra/evals approach
# ============================================================================

"""
# Old ml-infra/evals code (pseudo-code):

import pandas as pd
from ml_infra_evals import load_data_from_index, call_aidevops_service, add_metric

# Load dataset
dataset = load_data_from_index(
    "benchmarks/datasets/index.csv",
    entity_type="pipeline",
    operation_type="create",
)

# Generate outputs
results_df = call_aidevops_service(
    dataset,
    model="claude-3-7-sonnet-20250219",
    base_url="http://localhost:8000",
)

# Add metrics
results_df = add_metric(results_df, "deep_diff_v3")
results_df = add_metric(results_df, "deep_diff_v2")

# Save results
results_df.to_csv("results/pipeline_create.csv", index=False)
"""

# ============================================================================
# AFTER: AI Evolution SDK approach
# ============================================================================

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from aieval import (
    Experiment,
    HTTPAdapter,
    DeepDiffScorer,
    load_index_csv_dataset,
    CSVSink,
)
from samples_sdk.consumers.devops import run_devops_eval, create_devops_eval


async def migration_example_simple():
    """Simple migration - using helper function."""
    print("=== Simple Migration (Helper Function) ===")
    
    # One-line equivalent to ml-infra/evals workflow
    result = await run_devops_eval(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        model="claude-3-7-sonnet-20250219",
        base_url="http://localhost:8000",
        auth_token="your-token",
        output_csv="results/pipeline_create.csv",
    )
    
    print(f"Evaluation completed: {result.run_id}")


async def migration_example_detailed():
    """Detailed migration - step by step."""
    print("\n=== Detailed Migration (Step by Step) ===")
    
    # Step 1: Load dataset (equivalent to load_data_from_index)
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    print(f"Loaded {len(dataset)} test cases")
    
    # Step 2: Create scorers (equivalent to add_metric)
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
        DeepDiffScorer(name="deep_diff_v2", eval_id="deep_diff_v2.v1", version="v2"),
    ]
    
    # Step 3: Create experiment
    experiment = Experiment(
        name="pipeline_creation_benchmark",
        dataset=dataset,
        scorers=scorers,
    )
    
    # Step 4: Create adapter using HTTPAdapter with ml-infra configuration
    # Teams should create their own custom adapters - this is just an example
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        auth_token="your-token",
        context_field_name="context",
        context_data={
            "account_id": "account-123",
            "org_id": "org-456",
            "project_id": "project-789",
        },
        endpoint_mapping={
            "dashboard": "/chat/dashboard",
            "knowledge_graph": "/chat/knowledge-graph",
        },
        default_endpoint="/chat/platform",
        yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
        sse_completion_events=["dashboard_complete", "kg_complete"],
    )
    
    # Step 5: Run eval (equivalent to call_aidevops_service + add_metric)
    result = await eval_.run(
        adapter=adapter,
        model="claude-3-7-sonnet-20250219",
        concurrency_limit=5,
    )
    
    # Step 6: Save results (equivalent to to_csv)
    csv_sink = CSVSink("results/pipeline_create.csv")
    csv_sink.emit_run(result)
    csv_sink.flush()
    
    print(f"Evaluation completed: {result.run_id}")
    print(f"Total scores: {len(result.scores)}")


async def migration_example_offline():
    """Offline evaluation migration."""
    print("\n=== Offline Evaluation Migration ===")
    
    # Old: python3 benchmark_evals.py --use-index --offline --actual-suffix generated
    
    # New: Using SDK
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        offline=True,  # Enable offline mode
        actual_suffix="generated",  # Use *_generated.yaml files
    )
    
    eval_ = create_devops_eval(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        offline=True,
        actual_suffix="generated",
    )
    
    # Score pre-generated outputs (no adapter needed)
    from aieval.core.types import ExperimentRun
    import uuid
    
    all_scores = []
    for item in dataset:
        if item.output:
            for scorer in eval_.scorers:
                score = scorer.score(
                    generated=item.output,
                    expected=item.expected,
                    metadata=item.metadata,
                )
                all_scores.append(score)
    
    run = Run(
        eval_id=str(uuid.uuid4()),
        run_id=str(uuid.uuid4()),
        dataset_id="offline",
        scores=all_scores,
    )
    
    csv_sink = CSVSink("results/pipeline_offline.csv")
    csv_sink.emit_run(run)
    csv_sink.flush()
    
    print(f"Offline evaluation completed: {len(all_scores)} scores")


async def migration_example_multi_model():
    """Multi-model comparison migration."""
    print("\n=== Multi-Model Comparison Migration ===")
    
    # Old: Run benchmark_evals.py multiple times with different models
    
    # New: Run once per model and compare
    models = ["claude-3-7-sonnet-20250219", "gpt-4o"]
    runs = []
    
    for model in models:
        result = await run_devops_eval(
            index_file="benchmarks/datasets/index.csv",
            base_dir="benchmarks/datasets",
            entity_type="pipeline",
            operation_type="create",
            model=model,
            output_csv=f"results/pipeline_{model}.csv",
        )
        runs.append(result)
    
    # Compare runs
    if len(runs) >= 2:
        from aieval import compare_runs
        comparison = compare_runs(runs[0], runs[1])
        print(f"Model comparison: {comparison.improvements} improvements, {comparison.regressions} regressions")


if __name__ == "__main__":
    print("Migration examples (before/after comparison)")
    print("Uncomment to run:")
    # asyncio.run(migration_example_simple())
    # asyncio.run(migration_example_detailed())
    # asyncio.run(migration_example_offline())
    # asyncio.run(migration_example_multi_model())
