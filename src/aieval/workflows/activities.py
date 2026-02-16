"""Temporal activities for AI Evolution Platform.

Activities are the actual work units that execute in Temporal workflows.
They can be retried automatically and are idempotent.
"""

import logging
from typing import Any

from temporalio import activity
from temporalio.common import RetryPolicy

from aieval.core.eval import Eval
from aieval.core.types import DatasetItem, Score, EvalResult
from aieval.datasets import load_jsonl_dataset, load_index_csv_dataset
from aieval.adapters.base import Adapter
from aieval.scorers.base import Scorer

logger = logging.getLogger(__name__)

# Retry policy for activities
ACTIVITY_RETRY_POLICY = RetryPolicy(
    initial_interval=1.0,  # 1 second
    backoff_coefficient=2.0,
    maximum_interval=60.0,  # 60 seconds
    maximum_attempts=5,
)


@activity.defn(name="load_dataset")
async def load_dataset_activity(config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Load dataset from configuration.
    
    This activity is idempotent - loading the same dataset multiple times
    produces the same result.
    
    Args:
        config: Dataset configuration
        
    Returns:
        List of dataset items as dictionaries
    """
    activity.logger.info(f"Loading dataset: {config.get('type')}")
    
    dataset_config = config.get("dataset", {})
    dataset_type = dataset_config.get("type", "jsonl")
    
    try:
        if dataset_type == "jsonl":
            dataset = load_jsonl_dataset(dataset_config.get("path"))
        elif dataset_type == "index_csv":
            dataset = load_index_csv_dataset(
                index_file=dataset_config.get("index_file"),
                base_dir=dataset_config.get("base_dir"),
                entity_type=dataset_config.get("filters", {}).get("entity_type"),
                operation_type=dataset_config.get("filters", {}).get("operation_type"),
            )
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        
        # Convert to dict for serialization
        dataset_dicts = [item.to_dict() for item in dataset]
        activity.logger.info(f"Loaded {len(dataset_dicts)} items")
        return dataset_dicts
        
    except Exception as e:
        activity.logger.error(f"Failed to load dataset: {e}")
        raise


@activity.defn(name="run_experiment")
async def run_experiment_activity(
    dataset_items: list[dict[str, Any]],
    scorers_config: list[dict[str, Any]],
    adapter_config: dict[str, Any],
    model: str | None = None,
    concurrency_limit: int = 5,
) -> dict[str, Any]:
    """
    Run experiment with given configuration.
    
    Args:
        dataset_items: Dataset items (as dicts)
        scorers_config: Scorer configurations
        adapter_config: Adapter configuration
        model: Model name (optional)
        concurrency_limit: Maximum concurrent API calls
        
    Returns:
        EvalResult as dictionary
    """
    activity.logger.info(f"Running experiment with {len(dataset_items)} items")
    
    # Convert dataset items back from dicts
    dataset = [
        DatasetItem(
            id=item["id"],
            input=item["input"],
            expected=item.get("expected"),
            tags=item.get("tags", []),
            metadata=item.get("metadata", {}),
        )
        for item in dataset_items
    ]
    
    # Create scorers (simplified - in production, use scorer factory)
    from aieval.scorers.deep_diff import DeepDiffScorer
    scorers: list[Scorer] = []
    for scorer_config in scorers_config:
        if scorer_config.get("type") == "deep_diff":
            scorers.append(
                DeepDiffScorer(
                    name=f"deep_diff_{scorer_config.get('version', 'v3')}",
                    eval_id=f"deep_diff_{scorer_config.get('version', 'v3')}.v1",
                    version=scorer_config.get("version", "v3"),
                )
            )
    
    # Create adapter (simplified - in production, use adapter factory)
    from aieval.adapters.http import HTTPAdapter
    adapter = HTTPAdapter(
        base_url=adapter_config.get("base_url", "http://localhost:8000"),
        auth_token=adapter_config.get("auth_token", ""),
    )
    
    # Create and run eval
    eval_ = Eval(
        name="temporal_eval",
        dataset=dataset,
        scorers=scorers,
    )
    
    result = await eval_.run(
        adapter=adapter,
        model=model,
        concurrency_limit=concurrency_limit,
    )
    
    # Convert to dict for serialization
    return result.to_dict()


@activity.defn(name="score_item")
async def score_item_activity(
    generated: str,
    expected: dict[str, Any] | None,
    scorer_config: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Score a single item with a scorer.
    
    Args:
        generated: Generated output
        expected: Expected output
        scorer_config: Scorer configuration
        metadata: Additional metadata
        
    Returns:
        Score as dictionary
    """
    # Create scorer and score
    from aieval.scorers.deep_diff import DeepDiffScorer
    
    scorer = DeepDiffScorer(
        name=scorer_config.get("name", "deep_diff"),
        eval_id=scorer_config.get("eval_id", "deep_diff.v1"),
        version=scorer_config.get("version", "v3"),
    )
    
    score = scorer.score(generated, expected, metadata)
    return score.to_dict()


@activity.defn(name="emit_results")
async def emit_results_activity(
    result: dict[str, Any],
    sinks_config: list[dict[str, Any]],
) -> None:
    """
    Emit experiment results to sinks.
    
    Args:
        result: Run as dictionary
        sinks_config: Sink configurations
    """
    activity.logger.info(f"Emitting results to {len(sinks_config)} sinks")
    
    from aieval.core.types import EvalResult
    from aieval.sinks.csv import CSVSink
    from aieval.sinks.json import JSONSink
    from aieval.sinks.stdout import StdoutSink
    
    # Convert result back to EvalResult
    run = EvalResult(
        eval_id=result["eval_id"],
        run_id=result["run_id"],
        dataset_id=result["dataset_id"],
        scores=[],  # Would need to reconstruct scores
        metadata=result.get("metadata", {}),
    )
    
    # Create sinks and emit
    sinks = []
    for sink_config in sinks_config:
        sink_type = sink_config.get("type")
        if sink_type == "csv":
            sinks.append(CSVSink(sink_config.get("path", "results.csv")))
        elif sink_type == "json":
            sinks.append(JSONSink(sink_config.get("path", "results.json")))
        elif sink_type == "stdout":
            sinks.append(StdoutSink())
    
    for sink in sinks:
        sink.emit_run(run)
        sink.flush()
