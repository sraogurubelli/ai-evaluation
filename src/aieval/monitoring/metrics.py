"""Prometheus metrics for AI Evolution Platform."""

import time
from functools import wraps
from typing import Any, Callable

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from starlette.responses import Response

# Request metrics
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

request_errors = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    ["method", "endpoint", "error_type"],
)

# Eval metrics
eval_runs_total = Counter(
    "eval_runs_total",
    "Total eval runs",
    ["eval_id", "status"],
)

eval_runs_failed = Counter(
    "eval_runs_failed_total",
    "Total failed eval runs",
    ["eval_id", "error_type"],
)

eval_duration = Histogram(
    "eval_duration_seconds",
    "Eval execution duration in seconds",
    ["eval_id"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

# Task metrics
task_count = Gauge(
    "tasks_total",
    "Current number of tasks",
    ["status"],
)

task_duration = Histogram(
    "task_duration_seconds",
    "Task execution duration in seconds",
    ["task_type", "status"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

# Database metrics
database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation", "table"],
)

database_query_duration = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0],
)

database_connections = Gauge(
    "database_connections",
    "Current number of database connections",
    ["state"],
)

# Adapter metrics
adapter_requests_total = Counter(
    "adapter_requests_total",
    "Total adapter requests",
    ["adapter_type", "status"],
)

adapter_request_duration = Histogram(
    "adapter_request_duration_seconds",
    "Adapter request duration in seconds",
    ["adapter_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Scorer metrics
scorer_executions_total = Counter(
    "scorer_executions_total",
    "Total scorer executions",
    ["scorer_type", "status"],
)

scorer_duration = Histogram(
    "scorer_duration_seconds",
    "Scorer execution duration in seconds",
    ["scorer_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)


def get_metrics_registry():
    """Get Prometheus metrics registry."""
    return REGISTRY


async def metrics_middleware(request: Any, call_next: Callable):
    """Middleware to track request metrics."""
    start_time = time.time()

    # Extract endpoint (simplified)
    endpoint = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        status_code = response.status_code

        # Record metrics
        duration = time.time() - start_time
        request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration)

        request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        if status_code >= 400:
            request_errors.labels(
                method=method,
                endpoint=endpoint,
                error_type=f"{status_code // 100}xx",
            ).inc()

        return response
    except Exception as e:
        duration = time.time() - start_time
        request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=500,
        ).observe(duration)

        request_errors.labels(
            method=method,
            endpoint=endpoint,
            error_type=type(e).__name__,
        ).inc()

        raise


async def metrics_endpoint(request: Any) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
