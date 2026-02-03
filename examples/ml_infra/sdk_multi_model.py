"""Example: ML Infra Multi-Model Comparison using SDK.

This demonstrates how to compare multiple models similar to ml-infra/evals.
Run from repo root with PYTHONPATH=.
"""

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
    StdoutSink,
    compare_runs,
)
from samples_sdk.consumers.devops import create_devops_experiment, create_devops_sinks, run_devops_eval


async def example_multi_model_comparison():
    """Compare multiple models on the same dataset."""
    print("=== ML Infra Multi-Model Comparison ===")
    
    # Load dataset
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    
    # Create scorers
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
    ]
    
    # Models to compare
    models = [
        "claude-3-7-sonnet-20250219",
        "gpt-4o",
    ]
    
    # Create adapter (HTTPAdapter with ml-infra context)
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        auth_token="your-token",
        context_field_name="harness_context",
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
    )
    
    runs = []
    
    # Run experiment for each model
    for model in models:
        print(f"\nRunning evaluation for model: {model}")
        
        experiment = Experiment(
            name=f"pipeline_creation_{model}",
            dataset=dataset,
            scorers=scorers,
        )
        
        result = await experiment.run(
            adapter=adapter,
            model=model,
            concurrency_limit=5,
        )
        
        runs.append(result)
        
        # Save results to CSV
        csv_sink = CSVSink(f"results/pipeline_{model}.csv")
        csv_sink.emit_run(result)
        csv_sink.flush()
    
    # Compare runs
    if len(runs) >= 2:
        print("\n=== Comparing Models ===")
        comparison = compare_runs(runs[0], runs[1])
        
        print(f"Model 1: {runs[0].run_id}")
        print(f"Model 2: {runs[1].run_id}")
        print(f"\nImprovements: {comparison.improvements}")
        print(f"Regressions: {comparison.regressions}")
        print(f"Unchanged: {comparison.unchanged}")


async def example_multi_model_using_helper():
    """Using helper function for multi-model comparison."""
    print("\n=== Using Helper Function ===")
    
    # run_devops_eval imported at top from samples_sdk.consumers.devops
    
    models = ["claude-3-7-sonnet-20250219", "gpt-4o"]
    
    for model in models:
        result = await run_devops_eval(
            index_file="benchmarks/datasets/index.csv",
            base_dir="benchmarks/datasets",
            entity_type="pipeline",
            operation_type="create",
            model=model,
            output_csv=f"results/pipeline_{model}.csv",
        )
        print(f"Completed evaluation for {model}: {result.run_id}")


if __name__ == "__main__":
    # asyncio.run(example_multi_model_comparison())
    # asyncio.run(example_multi_model_using_helper())
    print("Multi-model comparison examples (requires ml-infra server)")
