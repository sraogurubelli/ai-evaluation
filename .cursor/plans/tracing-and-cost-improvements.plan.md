---
name: ""
overview: ""
todos: []
isProject: false
---

# Plan: Tracing and cost improvements (BYOT, cost extraction)

**Source:** [AI_EVALUATION_IMPROVEMENTS_DESIGN.md](../../AI_EVALUATION_IMPROVEMENTS_DESIGN.md), [AI_EVALUATION_IMPLEMENTATION_PLAN.md](../../AI_EVALUATION_IMPLEMENTATION_PLAN.md)

**Status:** For team review before implementation.

---

## 1. Overview

Enable "Bring Your Own Tracing" and cost extraction in ai-evaluation: define a **TracingAdapter** interface to read traces from the user's system (Langfuse, OpenTelemetry/Jaeger), extract cost/token data, and optionally propagate trace linkage through the evaluation flow. SynteraIQ (and other consumers) can use these adapters; cost persistence and canary UI stay in SynteraIQ.

---

## 2. Decisions for review

| Decision | Proposal | Notes |

|----------|----------|--------|

| **Cost placement** | Support both: **Score.metadata** (optional `cost`, `input_tokens`, `output_tokens`, `provider`, `model` per datapoint) and **ExperimentRun.metadata** (optional `aggregate_metrics: { accuracy, cost, latency_sec, input_tokens, output_tokens }`). | No DB migration; use existing JSON metadata. |

| **TracingAdapter vs Adapter** | New **TracingAdapter** is for *reading* traces (get_trace, get_cost_data, list_traces). Existing **Adapter** stays for *generating* outputs. | Two separate interfaces. |

| **Langfuse: two adapters** | **LangfuseAdapter** (adapters/langfuse.py): read *output* from trace for evaluation (implement `generate()`). **LangfuseTracingAdapter** (tracing/langfuse.py): read trace metadata and cost. | Different modules, different roles. |

| **Optional dependencies** | Tracing is optional: `pip install aieval` (no tracing); `aieval[tracing-langfuse]`, `aieval[tracing-otel]` for adapters. | Keeps core lightweight. |

| **Trace ID propagation** | Adapters may return `(output, metadata)` with `trace_id`/`observation_id`; or document pattern for caller to inject. HTTPAdapter: extract trace IDs from response when present. | Phase 3 detail. |

---

## 3. New module and types

- **Module:** `src/aieval/tracing/` (new).
- **Base:** `tracing/base.py` — abstract `TracingAdapter` with:
  - `get_trace(trace_id: str) -> Trace | None`
  - `get_cost_data(trace_id: str) -> CostData | None`
  - `list_traces(filters: dict, limit: int = 100) -> list[Trace]`
- **Types:** `Trace`, `Span`, `CostData` dataclasses (reference: agent-eval `sdks/python/agenteval/tracing/types.py`).
- **Conventions:** `tracing/conventions.py` — OTel/Langfuse attribute names (`llm.token_count.input`, `llm.cost`, etc.) and helper `extract_cost_from_span_attributes(attrs) -> CostData | None`.

---

## 4. Phased deliverables

### Phase 0: Contracts and conventions (foundation)

- [x] Create `aieval/tracing/` with `base.py` (TracingAdapter, Trace, Span, CostData).
- [x] Create `conventions.py` (attribute names, cost extraction helper).
- [x] Document Score/Run metadata for cost in `core/types.py` and `docs/tracing.md`.
- [x] Update `docs/architecture.md` for tracing integration.  

**Acceptance:** Interfaces importable; types defined; docs updated. No adapter implementation yet.

### Phase 1: Langfuse TracingAdapter

- [x] Implement `tracing/langfuse.py` — LangfuseTracingAdapter (get_trace, get_cost_data using Langfuse client).
- [x] Add optional extra `[tracing-langfuse]` in pyproject.toml; factory `create_tracing_adapter(adapter_type="langfuse", **config)`.
- [x] Config: `tracing.adapter`, `tracing.langfuse.*`; secrets from env (LANGFUSE_SECRET_KEY, etc.).  

**Acceptance:** Can instantiate LangfuseTracingAdapter, call get_trace/get_cost_data, get CostData. Integration test recommended.

### Phase 2: OpenTelemetry TracingAdapter

- [x] Implement `tracing/opentelemetry.py` — read from Jaeger HTTP API (`GET /api/traces/{id}`, `GET /api/traces`), extract cost from span attributes via conventions.
- [x] Add optional extra `[tracing-otel]` (e.g. httpx).
- [x] Config: `adapter_type="opentelemetry"`, `tracing.opentelemetry.endpoint`.  

**Acceptance:** Same as Phase 1 for OTel backend; works with Jaeger HTTP API.

### Phase 3: SDK integration and Langfuse adapter completion

- [x] Adapter return: `GenerateResult(output, trace_id=None, observation_id=None)`; `normalize_adapter_output()`; flow from adapter → Score in experiment and runner.
- [x] LangfuseAdapter (adapters/langfuse.py): implement `generate()` — fetch trace, extract assistant output, return GenerateResult (evaluate against prod traces).
- [x] Optional: helper `enrich_run_aggregate_metrics(run, tracing_adapter)` in `tracing/aggregates.py`; populate `ExperimentRun.metadata["aggregate_metrics"]`.  

**Acceptance:** LangfuseAdapter.generate() works; trace IDs propagate; run metadata can include aggregates.

---

## 5. Configuration (for review)

```yaml
tracing:
  adapter: langfuse  # or opentelemetry, none
  langfuse:
    host: ${LANGFUSE_HOST:-https://cloud.langfuse.com}
    # secret_key, public_key from env
  opentelemetry:
    endpoint: http://jaeger:16686
```

- Document in README and `docs/tracing.md`; `.env.example` with LANGFUSE_*, tracing vars.

---

## 6. Out of scope (confirm with team)

- SynteraIQ-specific features (cost API, canary analysis, product UI).
- Agent-eval backend cost persistence / canary API.
- Prompt Registry, AgentDeploy.
- Custom TracingAdapter implementations beyond Langfuse and OTel (users can add their own).
- Database schema changes for cost (use existing JSON columns).

---

## 7. Acceptance criteria (summary)

- [ ] TracingAdapter interface and types defined and documented.
- [ ] LangfuseTracingAdapter implemented and tested.
- [ ] OpenTelemetryAdapter implemented and tested.
- [ ] Optional extras: `pip install aieval[tracing-langfuse]`, `aieval[tracing-otel]`.
- [ ] Config supports tracing adapter selection; secrets from env.
- [ ] LangfuseAdapter (adapters) can read output from trace (generate()).
- [ ] Score and Run metadata documented for cost; aggregate_metrics optional.
- [ ] Documentation updated (README, docs/tracing.md, docs/architecture.md).

---

## 8. Reference

- **Tracing types:** agent-eval `sdks/python/agenteval/tracing/` (types.py, base.py, langfuse_adapter.py, opentelemetry_adapter.py).
- **Existing in ai-evaluation:** `src/aieval/sinks/langfuse.py`, `src/aieval/adapters/langfuse.py`.