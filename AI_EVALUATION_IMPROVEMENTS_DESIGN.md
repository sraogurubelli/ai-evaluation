# AI-Evaluation Improvements Design

**Purpose:** Design document for improving the open-source ai-evaluation framework. These improvements enable "Bring Your Own Tracing," cost extraction from traces, and better integration with consuming platforms.

---

## Current State Summary

| Component | Status |
|-----------|--------|
| **Score** (core/types.py, db/models.py) | ✅ Has `trace_id`, `observation_id` for Langfuse linking |
| **LangfuseSink** | ✅ Sends scores to Langfuse |
| **LangfuseAdapter** (adapters/langfuse.py) | ❌ Placeholder; `generate()` raises NotImplementedError |
| **OpenTelemetry** (monitoring/tracing.py) | ✅ Internal tracing for ai-evaluation (FastAPI, SQLAlchemy) |
| **Adapter** base | For *generating* outputs (HTTP, etc.) — not for *reading* traces |
| **Cost tracking** | ❌ Not present in ai-evaluation |

---

## Design: Improvement Opportunities

### 1. TracingAdapter Interface (Read from User's Tracing)

**Goal:** Allow ai-evaluation to *read* traces from the user's existing tracing system (OpenTelemetry, Langfuse, custom). This is distinct from the current `Adapter`, which *generates* outputs.

**New module:** `aieval.tracing/` (or `aieval.tracing_adapters/` to avoid confusion with monitoring.tracing)

**Interface:**

```python
# aieval/tracing/base.py
from abc import ABC, abstractmethod
from typing import Any

class TracingAdapter(ABC):
    """Adapter for reading traces from user's tracing system (OTel, Langfuse, etc.)."""

    @abstractmethod
    def get_trace(self, trace_id: str) -> Trace | None:
        """Get trace by ID."""
        pass

    @abstractmethod
    def get_cost_data(self, trace_id: str) -> CostData | None:
        """Extract cost data from trace (tokens, provider, cost)."""
        pass

    @abstractmethod
    def list_traces(self, filters: dict[str, Any], limit: int = 100) -> list[Trace]:
        """List traces matching filters."""
        pass
```

**Types:** `Trace`, `Span`, `CostData` dataclasses (see agent-eval implementation for reference).

**Why in ai-evaluation:** Framework-level support for "evaluation linked to trace" and cost extraction. SynteraIQ/agent-eval can depend on ai-evaluation and use these adapters.

---

### 2. Implement OpenTelemetryAdapter

**Goal:** Read traces from OpenTelemetry backends (Jaeger, Tempo, Grafana Cloud, etc.).

**Implementation notes:**
- Use Jaeger-style HTTP API: `GET /api/traces/{trace_id}`, `GET /api/traces` with query params
- Or OTLP/gRPC if available
- Extract cost from span attributes: `llm.token_count.input`, `llm.token_count.output`, `llm.cost`, `llm.provider`, `llm.model` (OpenTelemetry semantic conventions for LLM)
- Dependencies: `httpx` (optional, for HTTP); keep ai-evaluation lightweight

**Location:** `aieval/tracing/opentelemetry.py`

---

### 3. Complete LangfuseAdapter (Adapters) + Add LangfuseTracingAdapter (Tracing)

**Two separate things:**

| Name | Purpose | Location |
|------|---------|----------|
| **LangfuseAdapter** (existing) | Read *output* from Langfuse trace to use as generated output for evaluation | `aieval/adapters/langfuse.py` |
| **LangfuseTracingAdapter** (new) | Read *trace metadata, cost* from Langfuse for cost extraction & linking | `aieval/tracing/langfuse.py` |

**LangfuseAdapter (adapters):** Implement `generate()` to fetch a trace from Langfuse, extract the assistant output (or final observation content), and return it. Enables "evaluate against prod traces" workflow.

**LangfuseTracingAdapter (tracing):** Use Langfuse Python client to get trace by ID, extract `total_cost`, token usage, model from trace/observations.

---

### 4. CostData and Run-Level Cost Aggregation

**Goal:** ai-evaluation runs can optionally carry cost data from traces.

**Options:**
- **A) Minimal:** Add `cost_data: list[CostData] | None` to `ExperimentRun` metadata (or a new optional field). No DB schema change; cost lives in metadata.
- **B) First-class:** Add `run_costs` table or `cost` JSON column to `experiment_runs`. Enables queries and canary comparison.

**Recommendation:** Start with A (metadata). SynteraIQ can persist costs in its own DB; ai-evaluation just needs to support passing cost data through the run.

**Score enrichment:** When a score has `trace_id`, a TracingAdapter can be used to fetch cost and attach it to the score metadata or run metadata.

---

### 5. SDK: Pass trace_id / observation_id Through Evaluation Flow

**Goal:** Ensure trace linkage works end-to-end when the user's app (or adapter) provides trace/observation IDs.

**Current flow:** Scorers produce `Score`; runner can convert ai-evals format (with trace_id, observation_id) to EvolutionScore. HTTPAdapter does not return trace_id.

**Improvements:**
- **Adapter contract:** Allow adapters to return `(output, metadata)` where metadata can include `trace_id`, `observation_id`. Or add optional `get_trace_context() -> dict` to Adapter.
- **Adapter.generate()** could return a richer type, e.g. `GenerateResult(output, trace_id=None, observation_id=None)`.
- **HTTPAdapter:** If the API returns `trace_id`/`observation_id` in response headers or JSON, extract and propagate.

**Alternative:** Keep adapter simple; let the *caller* (e.g. SynteraIQ) inject trace_id/observation_id into dataset items or experiment context. Document this pattern.

---

### 6. OpenTelemetry Semantic Conventions for LLM

**Goal:** Document and support standard attribute names for cost extraction.

**Standard attributes (from OTel LLM semantic conventions):**
- `llm.token_count.input` / `llm.token_count.output` (or `llm.tokens.input` / `llm.tokens.output`)
- `llm.model`
- `llm.provider`
- `llm.cost` (if pre-calculated)

**Action:** Add `aieval/tracing/conventions.py` with constants and a helper to extract cost from span attributes. TracingAdapter implementations use these.

---

### 7. ExperimentRun: Latency and Aggregate Metrics

**Goal:** Support canary-style comparison (base vs canary) with latency, cost, accuracy.

**Current:** `TaskResult` has `execution_time_seconds`; `ExperimentRun` has scores.

**Improvements:**
- Ensure `ExperimentRun` (or its serialization) exposes `execution_time` / `latency` when available.
- Add optional `aggregate_metrics: dict` to run metadata: `{"accuracy": 0.92, "cost": 0.05, "latency_sec": 12.3}`.
- Document how SynteraIQ can compute and attach these from scores + tracing.

---

### 8. Configuration: Tracing Adapter Selection

**Goal:** Users configure which tracing system to use without code changes.

**Config example (config.yml):**
```yaml
tracing:
  adapter: opentelemetry  # or langfuse, none
  opentelemetry:
    endpoint: http://jaeger:16686
  langfuse:
    host: https://cloud.langfuse.com
    # api key from env
```

**CLI / API:** When running experiments, optionally pass tracing adapter config. Cost extraction uses it when scores have trace_id.

---

## Implementation Order

| Phase | Items | Effort |
|-------|-------|--------|
| 1 | TracingAdapter interface + Trace/Span/CostData types | Small |
| 2 | OpenTelemetryAdapter (read from Jaeger HTTP API) | Medium |
| 3 | LangfuseTracingAdapter (read cost from Langfuse) | Medium |
| 4 | Complete LangfuseAdapter (adapters) — read output from trace | Medium |
| 5 | SDK: propagate trace_id/observation_id; optional GenerateResult | Small |
| 6 | OTel conventions + cost extraction helper | Small |
| 7 | Run-level cost/latency in metadata; config for tracing | Small |

---

## What Stays in SynteraIQ (This Workspace)

- **Cost persistence** — CostRecord table, CostTrackingService, cost API
- **Canary analysis** — Compare runs, regression detection, canary API
- **Product UI** — agent-eval-ui (cost dashboard, canary dashboard)
- **Product backend** — FastAPI app that uses ai-evaluation + cost/canary services

SynteraIQ consumes ai-evaluation's TracingAdapters to extract cost, then stores and visualizes it.

---

## Dependencies and Compatibility

- **ai-evaluation** should remain installable with minimal deps. Tracing adapters can be optional extras:
  - `pip install aieval[tracing-otel]` — adds httpx, optional
  - `pip install aieval[tracing-langfuse]` — adds langfuse
- Default install: no tracing adapters; user plugs in their own or installs extras.

---

## Summary

| Improvement | Location | Owner |
|-------------|----------|-------|
| TracingAdapter interface, types | aieval/tracing/ | ai-evaluation |
| OpenTelemetryAdapter | aieval/tracing/ | ai-evaluation |
| LangfuseTracingAdapter | aieval/tracing/ | ai-evaluation |
| Complete LangfuseAdapter (read output) | aieval/adapters/ | ai-evaluation |
| OTel conventions, cost extraction helper | aieval/tracing/ | ai-evaluation |
| SDK trace_id propagation | aieval/core, sdk | ai-evaluation |
| Config for tracing | config, cli | ai-evaluation |
| Cost persistence, canary, UI | agent-eval, agent-eval-ui | SynteraIQ (this workspace) |
