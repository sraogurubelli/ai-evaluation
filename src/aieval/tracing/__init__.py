"""Tracing adapters for reading traces and cost from external systems (BYOT).

Use TracingAdapter implementations to read traces from Langfuse or OpenTelemetry/Jaeger
and extract cost/token data. Distinct from adapters.Adapter (which generates outputs).

Optional: install aieval[tracing-langfuse] or aieval[tracing-otel] for adapter support.
"""

from aieval.tracing.base import CostData, Span, Trace, TracingAdapter
from aieval.tracing.factory import create_tracing_adapter
from aieval.tracing.langfuse import LangfuseTracingAdapter

__all__ = [
    "CostData",
    "LangfuseTracingAdapter",
    "Span",
    "Trace",
    "TracingAdapter",
    "create_tracing_adapter",
]
