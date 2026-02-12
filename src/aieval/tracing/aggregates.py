"""Helpers to compute run-level aggregate metrics from scores and tracing."""

from __future__ import annotations

from aieval.core.types import Run, Score
from aieval.tracing.base import CostData, TracingAdapter


def enrich_run_aggregate_metrics(
    run: Run,
    tracing_adapter: TracingAdapter | None,
) -> None:
    """
    Compute aggregate_metrics from run scores and optional tracing, and set run.metadata.

    If tracing_adapter is provided, cost/token data is fetched for each score that has
    trace_id. Aggregates include:
    - accuracy: mean of numeric score values (if any)
    - cost: sum of cost from tracing (and from score.metadata if present)
    - input_tokens, output_tokens: sums from tracing or score.metadata
    - latency_sec: not computed here (would require span timings)

    Modifies run.metadata["aggregate_metrics"] in place.
    """
    if tracing_adapter is None:
        _set_accuracy_only(run)
        return

    total_cost: float | None = None
    total_input = 0
    total_output = 0
    for score in run.scores:
        if score.trace_id:
            cost_data = tracing_adapter.get_cost_data(score.trace_id)
            if cost_data:
                if cost_data.cost is not None:
                    total_cost = (total_cost or 0) + cost_data.cost
                if cost_data.input_tokens is not None:
                    total_input += cost_data.input_tokens
                if cost_data.output_tokens is not None:
                    total_output += cost_data.output_tokens
        # Also sum from score.metadata if present
        if score.metadata:
            c = score.metadata.get("cost")
            if c is not None:
                try:
                    total_cost = (total_cost or 0) + float(c)
                except (TypeError, ValueError):
                    pass
            total_input += int(score.metadata.get("input_tokens") or 0)
            total_output += int(score.metadata.get("output_tokens") or 0)

    agg = _accuracy_dict(run)
    if total_cost is not None:
        agg["cost"] = total_cost
    if total_input > 0:
        agg["input_tokens"] = total_input
    if total_output > 0:
        agg["output_tokens"] = total_output
    run.metadata["aggregate_metrics"] = agg


def _accuracy_dict(run: Run) -> dict:
    """Compute accuracy (mean of score values) and return base aggregate dict."""
    numeric = [s.value for s in run.scores if isinstance(s.value, (int, float))]
    acc = sum(numeric) / len(numeric) if numeric else None
    d: dict = {}
    if acc is not None:
        d["accuracy"] = acc
    return d


def _set_accuracy_only(run: Run) -> None:
    """Set only accuracy in aggregate_metrics when no tracing adapter."""
    d = _accuracy_dict(run)
    if d:
        run.metadata["aggregate_metrics"] = d
