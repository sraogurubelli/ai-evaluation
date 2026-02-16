"""Langfuse TracingAdapter: read traces and cost from Langfuse via the Langfuse SDK."""

from __future__ import annotations

from typing import Any

from aieval.tracing.base import CostData, Span, Trace, TracingAdapter


def _get_langfuse_client(
    secret_key: str | None = None,
    public_key: str | None = None,
    host: str | None = None,
):
    """Return Langfuse client; uses env vars if args not provided."""
    import os
    from langfuse import Langfuse

    return Langfuse(
        secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY", ""),
        public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )


def _trace_to_dict(obj: Any) -> dict[str, Any]:
    """Convert Langfuse trace (object or dict) to a plain dict for safe access."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {k: getattr(obj, k, None) for k in dir(obj) if not k.startswith("_")}


def _aggregate_cost_from_observations(observations: list[Any]) -> CostData | None:
    """Sum input/output tokens and cost from a list of observations (e.g. generations)."""
    total_input = 0
    total_output = 0
    total_cost: float | None = None
    provider: str | None = None
    model: str | None = None

    for obs in observations or []:
        d = _trace_to_dict(obs) if not isinstance(obs, dict) else obs
        usage = d.get("usage") or d.get("input_usage") or {}
        if isinstance(usage, dict):
            total_input += int(usage.get("input", 0) or usage.get("input_tokens", 0) or 0)
            total_output += int(usage.get("output", 0) or usage.get("output_tokens", 0) or 0)
        c = d.get("total_cost") or d.get("cost")
        if c is not None:
            try:
                c = float(c)
                total_cost = (total_cost or 0) + c
            except (TypeError, ValueError):
                pass
        if not provider and d.get("model"):
            model = str(d["model"])
        if not provider and d.get("provider"):
            provider = str(d["provider"])

    if total_input == 0 and total_output == 0 and total_cost is None:
        return None
    return CostData(
        input_tokens=total_input if total_input else None,
        output_tokens=total_output if total_output else None,
        total_tokens=(total_input + total_output) if (total_input or total_output) else None,
        cost=total_cost,
        provider=provider,
        model=model,
    )


class LangfuseTracingAdapter(TracingAdapter):
    """Read traces and cost from Langfuse via the Langfuse Python SDK (api.trace, observations)."""

    def __init__(
        self,
        secret_key: str | None = None,
        public_key: str | None = None,
        host: str | None = None,
    ):
        """
        Initialize the adapter. Credentials can be passed or read from env (LANGFUSE_SECRET_KEY, etc.).
        """
        self._client = _get_langfuse_client(
            secret_key=secret_key,
            public_key=public_key,
            host=host,
        )

    def get_trace(self, trace_id: str) -> Trace | None:
        """Get trace by ID. Returns None if not found or on error."""
        try:
            raw = self._client.api.trace.get(trace_id)
        except Exception:
            return None
        d = _trace_to_dict(raw)
        if not d:
            return None

        trace_id_res = d.get("id") or trace_id
        name = d.get("name")
        metadata = {
            k: v for k, v in (d.get("metadata") or d.get("meta") or {}).items() if v is not None
        }
        spans: list[Span] = []

        # Map observations to spans if present
        for obs in d.get("observations") or []:
            o = _trace_to_dict(obs) if not isinstance(obs, dict) else obs
            span_id = o.get("id") or ""
            spans.append(
                Span(
                    span_id=span_id,
                    name=o.get("name") or "observation",
                    parent_id=o.get("parent_observation_id"),
                    start_time=o.get("start_time"),
                    end_time=o.get("end_time"),
                    attributes={
                        "total_cost": o.get("total_cost"),
                        "usage": o.get("usage"),
                        "model": o.get("model"),
                    },
                )
            )

        return Trace(
            trace_id=trace_id_res,
            name=name,
            spans=spans,
            metadata=metadata,
        )

    def get_cost_data(self, trace_id: str) -> CostData | None:
        """Extract cost/token data from the trace (and its observations). Returns None if not found."""
        trace = self.get_trace(trace_id)
        if trace is None:
            return None

        # Try trace-level total cost first (Langfuse can aggregate at trace level)
        try:
            raw = self._client.api.trace.get(trace_id)
        except Exception:
            return None
        d = _trace_to_dict(raw)

        total_cost = d.get("total_cost") or d.get("totalCost")
        if total_cost is not None:
            try:
                total_cost = float(total_cost)
            except (TypeError, ValueError):
                total_cost = None

        usage = d.get("usage") or d.get("total_usage")
        input_tokens = None
        output_tokens = None
        if isinstance(usage, dict):
            input_tokens = usage.get("input") or usage.get("input_tokens")
            output_tokens = usage.get("output") or usage.get("output_tokens")
            if input_tokens is not None:
                input_tokens = int(input_tokens)
            if output_tokens is not None:
                output_tokens = int(output_tokens)

        if total_cost is not None or input_tokens is not None or output_tokens is not None:
            total_tokens = None
            if input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
            elif input_tokens is not None:
                total_tokens = input_tokens
            elif output_tokens is not None:
                total_tokens = output_tokens
            return CostData(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost=total_cost,
                provider=str(d["provider"]) if d.get("provider") else None,
                model=str(d["model"]) if d.get("model") else None,
            )

        # Fallback: aggregate from observations
        observations = d.get("observations") or []
        return _aggregate_cost_from_observations(observations)

    def list_traces(
        self,
        filters: dict[str, Any],
        limit: int = 100,
    ) -> list[Trace]:
        """List traces matching filters. Supports Langfuse filter keys (e.g. user_id, session_id, tags)."""
        try:
            # Langfuse trace.list accepts limit, cursor, and filter params
            raw_list = self._client.api.trace.list(limit=limit, **filters)
        except Exception:
            return []

        result: list[Trace] = []
        items = (
            raw_list if isinstance(raw_list, list) else getattr(raw_list, "data", raw_list) or []
        )
        if not isinstance(items, list):
            items = []
        for raw in items:
            d = _trace_to_dict(raw)
            trace_id_res = d.get("id")
            if not trace_id_res:
                continue
            result.append(
                Trace(
                    trace_id=trace_id_res,
                    name=d.get("name"),
                    spans=[],
                    metadata={k: v for k, v in (d.get("metadata") or {}).items() if v is not None},
                )
            )
        return result
