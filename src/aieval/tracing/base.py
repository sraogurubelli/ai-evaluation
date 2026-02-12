"""Tracing adapter interface and types for BYOT (Bring Your Own Tracing).

TracingAdapter is for *reading* traces and cost from the user's tracing system
(Langfuse, OpenTelemetry/Jaeger). Distinct from adapters.Adapter (which generates outputs).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    """A single span within a trace."""

    span_id: str
    name: str
    parent_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """A trace (request/session) from the user's tracing backend."""

    trace_id: str
    name: str | None = None
    spans: list[Span] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostData:
    """Cost and token data extracted from a trace or span."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None
    provider: str | None = None
    model: str | None = None


class TracingAdapter(ABC):
    """Adapter for reading traces from the user's tracing system (OTel, Langfuse, etc.)."""

    @abstractmethod
    def get_trace(self, trace_id: str) -> Trace | None:
        """Get trace by ID. Returns None if not found."""
        pass

    @abstractmethod
    def get_cost_data(self, trace_id: str) -> CostData | None:
        """Extract cost/token data from trace. Returns None if not found or no cost data."""
        pass

    @abstractmethod
    def list_traces(
        self,
        filters: dict[str, Any],
        limit: int = 100,
    ) -> list[Trace]:
        """List traces matching filters. Backend-specific filter keys."""
        pass
