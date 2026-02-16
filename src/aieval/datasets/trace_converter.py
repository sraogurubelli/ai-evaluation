"""Convert production traces to datasets."""

from typing import Any
from datetime import datetime
import random

from aieval.core.types import DatasetItem
from aieval.evaluation.online import OnlineEvaluationAgent


def traces_to_dataset(
    traces: list[dict[str, Any]],
    trace_source: str = "langfuse",
    filters: dict[str, Any] | None = None,
    sample_size: int | None = None,
    sampling_strategy: str = "random",
) -> list[DatasetItem]:
    """
    Convert production traces to dataset items.
    
    Args:
        traces: List of trace dictionaries
        trace_source: Trace source ("langfuse", "otel", etc.)
        filters: Optional filters (by date, environment, etc.)
        sample_size: Optional sample size (if None, uses all traces)
        sampling_strategy: Sampling strategy ("random", "stratified")
        
    Returns:
        List of DatasetItem objects
    """
    # Apply filters
    filtered_traces = _apply_filters(traces, filters)
    
    # Apply sampling
    if sample_size is not None and sample_size < len(filtered_traces):
        filtered_traces = _sample_traces(filtered_traces, sample_size, sampling_strategy)
    
    # Convert to dataset items
    dataset_items = []
    for trace in filtered_traces:
        trace_id = trace.get("trace_id", trace.get("id", ""))
        trace_input = trace.get("input", {})
        trace_output = trace.get("output")
        
        dataset_item = DatasetItem(
            id=trace_id,
            input=trace_input,
            output=trace_output,
            expected=None,  # No expected output for production traces
            metadata={
                "trace_id": trace_id,
                "trace_source": trace_source,
                **trace.get("metadata", {}),
            },
        )
        dataset_items.append(dataset_item)
    
    return dataset_items


def _apply_filters(traces: list[dict[str, Any]], filters: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Apply filters to traces."""
    if not filters:
        return traces
    
    filtered = []
    for trace in traces:
        # Filter by date
        if "start_date" in filters or "end_date" in filters:
            trace_date = trace.get("created_at") or trace.get("timestamp")
            if trace_date:
                if isinstance(trace_date, str):
                    trace_date = datetime.fromisoformat(trace_date.replace("Z", "+00:00"))
                if "start_date" in filters:
                    start_date = filters["start_date"]
                    if isinstance(start_date, str):
                        start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    if trace_date < start_date:
                        continue
                if "end_date" in filters:
                    end_date = filters["end_date"]
                    if isinstance(end_date, str):
                        end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    if trace_date > end_date:
                        continue
        
        # Filter by environment
        if "environment" in filters:
            trace_env = trace.get("metadata", {}).get("environment") or trace.get("environment")
            if trace_env != filters["environment"]:
                continue
        
        # Filter by metadata keys
        if "metadata_keys" in filters:
            trace_metadata = trace.get("metadata", {})
            for key, value in filters["metadata_keys"].items():
                if trace_metadata.get(key) != value:
                    break
            else:
                filtered.append(trace)
                continue
            continue
        
        filtered.append(trace)
    
    return filtered


def _sample_traces(
    traces: list[dict[str, Any]],
    sample_size: int,
    strategy: str = "random",
) -> list[dict[str, Any]]:
    """Sample traces based on strategy."""
    if strategy == "random":
        return random.sample(traces, min(sample_size, len(traces)))
    elif strategy == "stratified":
        # Simple stratification by environment or other metadata
        # Group by environment
        groups: dict[str, list[dict[str, Any]]] = {}
        for trace in traces:
            env = trace.get("metadata", {}).get("environment") or trace.get("environment") or "default"
            groups.setdefault(env, []).append(trace)
        
        # Sample proportionally from each group
        sampled = []
        per_group = sample_size // len(groups) if groups else sample_size
        for group_traces in groups.values():
            sampled.extend(random.sample(group_traces, min(per_group, len(group_traces))))
        
        # Fill remaining slots randomly
        remaining = sample_size - len(sampled)
        if remaining > 0:
            remaining_traces = [t for t in traces if t not in sampled]
            sampled.extend(random.sample(remaining_traces, min(remaining, len(remaining_traces))))
        
        return sampled[:sample_size]
    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")
