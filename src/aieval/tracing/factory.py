"""Factory for creating TracingAdapter instances from config."""

from __future__ import annotations

from typing import Any

from aieval.tracing.base import TracingAdapter


def create_tracing_adapter(
    adapter_type: str = "langfuse",
    **config: Any,
) -> TracingAdapter | None:
    """
    Create a TracingAdapter by type.

    Args:
        adapter_type: One of "langfuse", "opentelemetry", or "none".
        **config: Adapter-specific options (e.g. secret_key, host for Langfuse;
                  endpoint for OpenTelemetry).

    Returns:
        TracingAdapter instance, or None if adapter_type is "none" or unknown.
    """
    if adapter_type is None or str(adapter_type).lower() == "none":
        return None

    kind = str(adapter_type).lower().strip()

    if kind == "langfuse":
        from aieval.tracing.langfuse import LangfuseTracingAdapter

        return LangfuseTracingAdapter(
            secret_key=config.get("secret_key"),
            public_key=config.get("public_key"),
            host=config.get("host"),
        )

    if kind == "opentelemetry":
        try:
            from aieval.tracing.opentelemetry import OpenTelemetryTracingAdapter
        except ImportError:
            return None
        endpoint = config.get("endpoint") or config.get("opentelemetry_endpoint") or ""
        if not endpoint:
            return None
        return OpenTelemetryTracingAdapter(endpoint=endpoint, timeout=config.get("timeout", 10.0))

    return None
