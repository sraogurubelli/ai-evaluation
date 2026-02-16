"""OpenTelemetry/Jaeger TracingAdapter: read traces and cost from Jaeger HTTP API."""

from __future__ import annotations

import urllib.parse
from typing import Any

from aieval.tracing.base import CostData, Span, Trace, TracingAdapter
from aieval.tracing.conventions import extract_cost_from_span_attributes

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]


def _tags_to_attributes(tags: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Convert Jaeger span tags (list of {key, value}) to a flat dict."""
    if not tags:
        return {}
    return {
        t["key"]: t["value"] for t in tags if isinstance(t, dict) and "key" in t and "value" in t
    }


class OpenTelemetryTracingAdapter(TracingAdapter):
    """
    Read traces from Jaeger via the HTTP query API (port 16686).

    Uses the internal JSON API: GET /api/traces/{traceID} and GET /api/traces.
    Cost is extracted from span attributes (OTel conventions) via
    extract_cost_from_span_attributes.
    """

    def __init__(self, endpoint: str, timeout: float = 10.0):
        """
        Initialize the adapter.

        Args:
            endpoint: Jaeger query base URL (e.g. http://localhost:16686).
            timeout: Request timeout in seconds.
        """
        if httpx is None:
            raise ImportError(
                "OpenTelemetry tracing adapter requires httpx. Install with: pip install aieval[tracing-otel]"
            )
        self._base = endpoint.rstrip("/")
        self._timeout = timeout

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        """GET JSON from Jaeger API."""
        url = f"{self._base}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    def get_trace(self, trace_id: str) -> Trace | None:
        """Get trace by ID. Returns None if not found or on error."""
        try:
            # Jaeger internal API: GET /api/traces/{traceID}
            data = self._get(f"/api/traces/{urllib.parse.quote(trace_id, safe='')}")
        except Exception:
            return None

        # Response can be { "data": [ { "traceID", "spans": [...] } ] } or direct list
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
        elif isinstance(data, dict) and data.get("data"):
            traces = data["data"]
            if not traces:
                return None
            first = traces[0]
        else:
            return None

        tid = first.get("traceID") or trace_id
        raw_spans = first.get("spans") or []
        spans = []
        for s in raw_spans:
            tags = s.get("tags") or []
            attrs = _tags_to_attributes(tags)
            spans.append(
                Span(
                    span_id=s.get("spanID", ""),
                    name=s.get("operationName", "span"),
                    parent_id=(s.get("references") or [{}])[0].get("spanID")
                    if s.get("references")
                    else None,
                    start_time=str(s["startTime"]) if s.get("startTime") is not None else None,
                    end_time=str(s["startTime"] + s["duration"])
                    if s.get("startTime") is not None and s.get("duration") is not None
                    else None,
                    attributes=attrs,
                )
            )
        return Trace(
            trace_id=tid,
            name=None,
            spans=spans,
            metadata={},
        )

    def get_cost_data(self, trace_id: str) -> CostData | None:
        """Extract cost/token data from trace spans using OTel conventions."""
        trace = self.get_trace(trace_id)
        if trace is None or not trace.spans:
            return None

        total_input = 0
        total_output = 0
        total_cost: float | None = None
        provider: str | None = None
        model: str | None = None

        for span in trace.spans:
            cost = extract_cost_from_span_attributes(span.attributes)
            if cost is None:
                continue
            if cost.input_tokens is not None:
                total_input += cost.input_tokens
            if cost.output_tokens is not None:
                total_output += cost.output_tokens
            if cost.cost is not None:
                total_cost = (total_cost or 0) + cost.cost
            if cost.provider and not provider:
                provider = cost.provider
            if cost.model and not model:
                model = cost.model

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

    def list_traces(
        self,
        filters: dict[str, Any],
        limit: int = 100,
    ) -> list[Trace]:
        """List traces. Supports Jaeger query params: service, limit, etc."""
        try:
            params: dict[str, Any] = {"limit": limit}
            if filters.get("service"):
                params["service"] = filters["service"]
            for key in ("start", "end", "lookback", "minDuration", "maxDuration", "operation"):
                if key in filters and filters[key] is not None:
                    params[key] = filters[key]
            data = self._get("/api/traces", params=params)
        except Exception:
            return []

        if isinstance(data, dict) and data.get("data"):
            traces_list = data["data"]
        elif isinstance(data, list):
            traces_list = data
        else:
            return []

        result = []
        for first in traces_list[:limit]:
            tid = first.get("traceID")
            if not tid:
                continue
            raw_spans = first.get("spans") or []
            spans = []
            for s in raw_spans:
                attrs = _tags_to_attributes(s.get("tags"))
                spans.append(
                    Span(
                        span_id=s.get("spanID", ""),
                        name=s.get("operationName", "span"),
                        parent_id=None,
                        start_time=str(s["startTime"]) if s.get("startTime") is not None else None,
                        end_time=None,
                        attributes=attrs,
                    )
                )
            result.append(Trace(trace_id=tid, name=None, spans=spans, metadata={}))
        return result
