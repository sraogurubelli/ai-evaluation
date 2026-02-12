"""Unit tests for tracing adapters and factory."""

import pytest

from aieval.tracing import (
    CostData,
    LangfuseTracingAdapter,
    Span,
    Trace,
    TracingAdapter,
    create_tracing_adapter,
)
from aieval.tracing.base import TracingAdapter as BaseTracingAdapter
from aieval.tracing.conventions import extract_cost_from_span_attributes


class TestCreateTracingAdapter:
    """Tests for create_tracing_adapter factory."""

    def test_none_returns_none(self):
        assert create_tracing_adapter("none") is None
        assert create_tracing_adapter(None) is None

    def test_langfuse_returns_adapter(self):
        adapter = create_tracing_adapter("langfuse")
        assert adapter is not None
        assert isinstance(adapter, TracingAdapter)
        assert isinstance(adapter, LangfuseTracingAdapter)

    def test_unknown_type_returns_none(self):
        assert create_tracing_adapter("unknown") is None


class TestLangfuseTracingAdapter:
    """Tests for LangfuseTracingAdapter with mocked client."""

    @pytest.fixture
    def mock_trace_response(self):
        return {
            "id": "trace-123",
            "name": "test-trace",
            "metadata": {"key": "value"},
            "total_cost": 0.002,
            "usage": {"input": 100, "output": 50},
        }

    @pytest.fixture
    def mock_trace_list_response(self):
        return [
            {"id": "trace-1", "name": "t1", "metadata": {}},
            {"id": "trace-2", "name": "t2", "metadata": {}},
        ]

    def test_get_trace_success(self, mock_trace_response):
        """get_trace returns Trace when API returns data."""
        adapter = LangfuseTracingAdapter(secret_key="sk", public_key="pk", host="http://localhost")
        adapter._client.api.trace.get = lambda tid: mock_trace_response if tid == "trace-123" else None

        trace = adapter.get_trace("trace-123")
        assert trace is not None
        assert trace.trace_id == "trace-123"
        assert trace.name == "test-trace"
        assert trace.metadata.get("key") == "value"

    def test_get_trace_not_found(self):
        """get_trace returns None when trace not found."""

        def raise_not_found(tid):
            raise Exception("not found")

        adapter = LangfuseTracingAdapter(secret_key="sk", public_key="pk", host="http://localhost")
        adapter._client.api.trace.get = raise_not_found

        trace = adapter.get_trace("missing")
        assert trace is None

    def test_get_cost_data_from_trace_level(self, mock_trace_response):
        """get_cost_data extracts cost from trace-level usage and total_cost."""
        adapter = LangfuseTracingAdapter(secret_key="sk", public_key="pk", host="http://localhost")
        adapter._client.api.trace.get = lambda tid: mock_trace_response if tid == "trace-123" else None

        cost = adapter.get_cost_data("trace-123")
        assert cost is not None
        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_tokens == 150
        assert cost.cost == 0.002

    def test_get_cost_data_not_found(self):
        """get_cost_data returns None when trace not found."""

        def raise_not_found(tid):
            raise Exception("not found")

        adapter = LangfuseTracingAdapter(secret_key="sk", public_key="pk", host="http://localhost")
        adapter._client.api.trace.get = raise_not_found

        assert adapter.get_cost_data("missing") is None

    def test_list_traces(self, mock_trace_list_response):
        """list_traces returns list of Trace from API list."""
        adapter = LangfuseTracingAdapter(secret_key="sk", public_key="pk", host="http://localhost")
        adapter._client.api.trace.list = lambda **kw: mock_trace_list_response

        traces = adapter.list_traces({}, limit=10)
        assert len(traces) == 2
        assert traces[0].trace_id == "trace-1"
        assert traces[1].trace_id == "trace-2"


class TestOpenTelemetryTracingAdapter:
    """Tests for OpenTelemetryTracingAdapter with mocked HTTP."""

    @pytest.fixture
    def mock_jaeger_trace_response(self):
        return {
            "data": [
                {
                    "traceID": "trace-abc",
                    "spans": [
                        {
                            "traceID": "trace-abc",
                            "spanID": "span-1",
                            "operationName": "llm",
                            "startTime": 1000,
                            "duration": 100,
                            "tags": [
                                {"key": "llm.token_count.input", "value": 50},
                                {"key": "llm.token_count.output", "value": 25},
                                {"key": "llm.cost", "value": 0.001},
                            ],
                        },
                    ],
                },
            ],
        }

    def test_otel_adapter_requires_httpx(self):
        """Without httpx, OpenTelemetryTracingAdapter raises ImportError (or we skip)."""
        try:
            from aieval.tracing.opentelemetry import OpenTelemetryTracingAdapter
        except ImportError:
            pytest.skip("httpx not installed")
        # With httpx installed, we can instantiate
        adapter = OpenTelemetryTracingAdapter("http://localhost:16686")
        assert adapter is not None

    def test_otel_get_trace_and_cost(self, mock_jaeger_trace_response):
        """get_trace and get_cost_data with mocked Jaeger response."""
        try:
            from aieval.tracing.opentelemetry import OpenTelemetryTracingAdapter
        except ImportError:
            pytest.skip("httpx not installed")
        import httpx

        def mock_get(path, params=None):
            return mock_jaeger_trace_response

        adapter = OpenTelemetryTracingAdapter("http://localhost:16686")
        adapter._get = mock_get

        trace = adapter.get_trace("trace-abc")
        assert trace is not None
        assert trace.trace_id == "trace-abc"
        assert len(trace.spans) == 1
        assert trace.spans[0].attributes.get("llm.token_count.input") == 50

        cost = adapter.get_cost_data("trace-abc")
        assert cost is not None
        assert cost.input_tokens == 50
        assert cost.output_tokens == 25
        assert cost.cost == 0.001


class TestConventions:
    """Tests for cost extraction conventions."""

    def test_extract_cost_otel_attrs(self):
        attrs = {
            "llm.token_count.input": 100,
            "llm.token_count.output": 50,
            "llm.cost": 0.001,
            "llm.model": "gpt-4",
        }
        cost = extract_cost_from_span_attributes(attrs)
        assert cost is not None
        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_tokens == 150
        assert cost.cost == 0.001
        assert cost.model == "gpt-4"

    def test_extract_cost_empty_returns_none(self):
        assert extract_cost_from_span_attributes({}) is None
        assert extract_cost_from_span_attributes(None) is None
