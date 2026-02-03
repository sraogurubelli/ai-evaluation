"""Example: ML Infra Offline Evaluation using SDK.

This demonstrates how to run offline evaluations (benchmarking pre-generated outputs)
similar to ml-infra/evals offline mode. Run from repo root with PYTHONPATH=.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from aieval import (
    Experiment,
    DeepDiffScorer,
    load_index_csv_dataset,
    CSVSink,
    StdoutSink,
)
from samples_sdk.consumers.devops import create_devops_experiment, create_devops_sinks


async def example_offline_evaluation():
    """Run offline evaluation on pre-generated outputs."""
    print("=== ML Infra Offline Evaluation Example ===")
    
    # Load dataset in offline mode (loads actual YAML files)
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        offline=True,  # Enable offline mode
        actual_suffix="actual",  # Look for *_actual.yaml files
    )
    
    print(f"Loaded {len(dataset)} test cases with pre-generated outputs")
    
    # Create scorers
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
        DeepDiffScorer(name="deep_diff_v2", eval_id="deep_diff_v2.v1", version="v2"),
        DeepDiffScorer(name="deep_diff_v1", eval_id="deep_diff_v1.v1", version="v1"),
    ]
    
    # Create experiment
    experiment = Experiment(
        name="pipeline_creation_offline",
        dataset=dataset,
        scorers=scorers,
    )
    
    # For offline mode, we score the pre-populated outputs directly
    # Note: In offline mode, we don't need an adapter since outputs are already in dataset
    # We'll need to modify Experiment.run() to handle this case, or score directly
    
    # Create sinks
    sinks = [
        StdoutSink(),
        CSVSink("results/pipeline_offline.csv"),
    ]
    
    # Score the outputs (since they're already in dataset.items[].output)
    from aieval.core.types import ExperimentRun
    import uuid
    from datetime import datetime
    
    all_scores = []
    for item in dataset:
        if item.output is None:
            print(f"Warning: Item {item.id} has no output (offline mode)")
            continue
        
        # Score with all scorers
        for scorer in scorers:
            score = scorer.score(
                generated=item.output,
                expected=item.expected,
                metadata=item.metadata,
            )
            all_scores.append(score)
    
    # Create experiment run
    run = ExperimentRun(
        experiment_id=str(uuid.uuid4()),
        run_id=str(uuid.uuid4()),
        dataset_id="offline_dataset",
        scores=all_scores,
        metadata={"mode": "offline", "entity_type": "pipeline"},
    )
    
    # Emit to sinks
    for sink in sinks:
        sink.emit_run(run)
        sink.flush()
    
    print(f"\nOffline evaluation completed: {len(all_scores)} scores generated")


async def example_offline_using_helper():
    """Using the ML Infra helper function for offline evaluation."""
    print("\n=== Using ML Infra Helper Function ===")
    
    # Create experiment using helper
    experiment = create_devops_experiment(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
        offline=True,
        actual_suffix="actual",
    )
    
    print(f"Created experiment: {experiment.name}")
    print(f"Dataset size: {len(experiment.dataset)}")
    print(f"Scorers: {[s.name for s in experiment.scorers]}")


if __name__ == "__main__":
    asyncio.run(example_offline_evaluation())
    # asyncio.run(example_offline_using_helper())
