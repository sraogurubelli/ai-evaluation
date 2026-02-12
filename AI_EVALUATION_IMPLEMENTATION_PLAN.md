# AI-Evaluation Implementation Plan

**Purpose:** Handoff document for implementing ai-evaluation improvements. Use this plan to review and implement changes in the ai-evaluation open-source repository.

**Target repo:** ai-evaluation

**Scope:** Plan and design only; implementation to be done per this document.

---

## 1. Ownership & Licensing

| Decision | Value |
|----------|-------|
| **Copyright** | Individual maintainer or project. Document in README and LICENSE. |
| **License** | MIT (already in place) |
| **CLA** | No CLA or project-specific contribution terms. |
| **Contributors** | Open; document in CONTRIBUTING.md. |

**Action:** Confirm ownership choice and ensure LICENSE + README reflect it. Add CONTRIBUTING.md if missing.

---

## 2. Cost Placement (Score vs Run)

**Decision:** Support both (Option C).

| Location | Use |
|----------|-----|
| **Score.metadata** | Optional `cost`, `input_tokens`, `output_tokens`, `provider`, `model` when cost is per-datapoint (one trace per item). |
| **ExperimentRun.metadata** | Optional `aggregate_metrics: { accuracy, cost, latency_sec, input_tokens, output_tokens }` for run-level summary. |

**Schema additions (design):**
- Document in `core/types.py` / API docs that `Score.metadata` may include cost-related keys.
- Document that `ExperimentRun.metadata` may include `aggregate_metrics`.
- No DB migration required if using existing JSON `meta` / `meta_data` columns.
- TracingAdapter implementations populate these when `trace_id` is present.

---

## 3. Phased Roadmap

### Phase 0: Contracts & Conventions (Foundation)

**Goal:** Define interfaces and standards. No heavy implementation.

**Deliverables:**

1. **TracingAdapter interface**
   - Location: `src/aieval/tracing/base.py` (new module)
   - Abstract base class with:
     - `get_trace(trace_id: str) -> Trace | None`
     - `get_cost_data(trace_id: str) -> CostData | None`
     - `list_traces(filters: dict, limit: int = 100) -> list[Trace]`
   - Types: `Trace`, `Span`, `CostData` dataclasses (see agent-eval `sdks/python/agenteval/tracing/types.py` for reference)

2. **OTel / Langfuse conventions**
   - Location: `src/aieval/tracing/conventions.py`
   - Constants: attribute names for `llm.token_count.input`, `llm.token_count.output`, `llm.provider`, `llm.model`, `llm.cost`, etc.
   - Helper: `extract_cost_from_span_attributes(attrs: dict) -> CostData | None`

3. **Documentation**
   - Update `docs/architecture.md` to mention tracing integration.
   - Add `docs/tracing.md` describing TracingAdapter, cost extraction, Score/Run metadata usage.

**Acceptance:** Interfaces importable; types defined; docs updated. No adapter implementation yet.

---

### Phase 1: Langfuse TracingAdapter (First Implementation)

**Goal:** Implement Langfuse as the first TracingAdapter. Langfuse first (per product decision).

**Deliverables:**

1. **LangfuseTracingAdapter**
   - Location: `src/aieval/tracing/langfuse.py`
   - Implements `TracingAdapter`
   - Uses Langfuse Python client to fetch trace by ID
   - Extracts cost from trace `total_cost`, observations, or span attributes
   - Maps Langfuse trace/observation to `Trace`, `Span`, `CostData` types

2. **Optional dependency**
   - In `pyproject.toml`: add optional extra `[tracing-langfuse]` with `langfuse` dependency
   - Core install: `pip install aieval` (no tracing)
   - With Langfuse: `pip install aieval[tracing-langfuse]`

3. **Factory / config**
   - `create_tracing_adapter(adapter_type: str, **config) -> TracingAdapter`
   - Supports `adapter_type="langfuse"` with `host`, `secret_key`, `public_key` (or from env)
   - Config example in `config.yml` or `.env.example`:
     ```yaml
     tracing:
       adapter: langfuse
       langfuse:
         host: ${LANGFUSE_HOST:-https://cloud.langfuse.com}
         # secret_key, public_key from env
     ```

**Acceptance:** Can instantiate LangfuseTracingAdapter, call `get_trace` and `get_cost_data`, get CostData for a trace. Integration test optional but recommended.

---

### Phase 2: OpenTelemetry TracingAdapter

**Goal:** Add OpenTelemetry/Jaeger as second TracingAdapter.

**Deliverables:**

1. **OpenTelemetryAdapter**
   - Location: `src/aieval/tracing/opentelemetry.py`
   - Reads from Jaeger HTTP API: `GET /api/traces/{id}`, `GET /api/traces`
   - Extracts cost from span attributes using `conventions.py`
   - Implements `TracingAdapter`

2. **Optional dependency**
   - `[tracing-otel]` extra with `httpx` (or similar)

3. **Config**
   - `adapter_type="opentelemetry"` with `endpoint` (e.g. `http://jaeger:16686`)

**Acceptance:** Same as Phase 1 for OTel backend. Works with Jaeger HTTP API.

---

### Phase 3: SDK Integration & Langfuse Adapter Completion

**Goal:** Wire trace linkage into evaluation flow; complete Langfuse adapter for reading output.

**Deliverables:**

1. **Adapter return type (optional)**
   - Consider `GenerateResult(output, trace_id=None, observation_id=None)` or allow adapters to return `(output, metadata)`.
   - Document how `trace_id` / `observation_id` flow from adapter → Score.
   - HTTPAdapter: if API returns trace IDs in response, extract and propagate.

2. **LangfuseAdapter (adapters/langfuse.py)**
   - Implement `generate()`: fetch trace from Langfuse, extract assistant output (or final observation content), return as string.
   - Use case: evaluate against production traces (replay).

3. **Run-level aggregates (optional)**
   - Add helper or hook to compute `aggregate_metrics` from scores + tracing when `trace_id` present.
   - Populate `ExperimentRun.metadata["aggregate_metrics"]` when possible.

**Acceptance:** LangfuseAdapter `generate()` works; trace IDs propagate; run metadata can include aggregates.

---

## 4. Hardening Plan

### 4.1 Code Quality

- [ ] Add type hints to new tracing code
- [ ] Add unit tests for TracingAdapter implementations
- [ ] Add integration test with mock Langfuse/OTel responses (or testcontainers if feasible)
- [ ] Lint and format (ruff, black, mypy per project norms)

### 4.2 Documentation

- [ ] README: mention tracing, cost extraction, optional extras
- [ ] `docs/tracing.md`: full tracing design and usage
- [ ] `docs/architecture.md`: update with tracing layer
- [ ] API docs: document new modules and public functions

### 4.3 Dependencies

- [ ] Core `aieval` has minimal deps; tracing is optional
- [ ] `langfuse` only required for `aieval[tracing-langfuse]`
- [ ] `httpx` only required for `aieval[tracing-otel]`

### 4.4 Configuration

- [ ] Document `tracing.adapter`, `tracing.langfuse.*`, `tracing.opentelemetry.*`
- [ ] Use env vars for secrets (LANGFUSE_SECRET_KEY, etc.)
- [ ] `.env.example` updated with tracing vars

---

## 5. Cleanup Plan

### 5.1 Audit (Do First)

Create a list of:
- All CLI commands and their usage status (implemented, placeholder, unused)
- All config options and whether they are used
- All adapters, sinks, scorers and their status
- Migration scripts and whether they are still needed

### 5.2 Deprecations

- [ ] Mark unimplemented CLI features (e.g. `compare`, `function` dataset) as deprecated or document as "not implemented"
- [ ] Add deprecation warnings for any APIs/config being phased out
- [ ] Set removal timeline (e.g. next major version) if applicable

### 5.3 Removals (After Deprecation Period)

- [ ] Remove dead code identified in audit
- [ ] Remove unused config options
- [ ] Consolidate duplicate logic where safe

### 5.4 Simplification

- [ ] Reduce config to minimal set: dataset, scorers, adapters, sinks, tracing
- [ ] Remove experimental or unfinished features that add confusion
- [ ] Update examples to use only supported features

### 5.5 Items to Keep

- Core: Experiment, Dataset, Scorers
- HTTPAdapter, LangfuseSink
- Score with trace_id, observation_id
- OpenTelemetry monitoring (for ai-evaluation service)
- API, CLI (implemented parts)
- DevOps consumer (if used)
- Existing sinks: CSV, JSON, stdout, JUnit, HTML report

---

## 6. Out of Scope (For This Plan)

- SynteraIQ-specific features (cost API, canary analysis, product UI)
- Agent-eval backend (cost persistence, canary API)
- Prompt Registry, AgentDeploy
- Custom TracingAdapter implementations beyond Langfuse and OTel (users can add their own)
- Database schema changes for cost (use existing JSON columns)

---

## 7. Implementation Order Checklist

| # | Task | Phase |
|---|------|-------|
| 1 | Confirm ownership; update LICENSE, README, CONTRIBUTING | Pre |
| 2 | Create `aieval/tracing/` module; define TracingAdapter, Trace, Span, CostData | 0 |
| 3 | Create `conventions.py` with attribute names and cost extraction helper | 0 |
| 4 | Document Score/Run metadata for cost; update architecture docs | 0 |
| 5 | Implement LangfuseTracingAdapter | 1 |
| 6 | Add `[tracing-langfuse]` extra; factory + config | 1 |
| 7 | Audit existing code; document deprecations | Cleanup |
| 8 | Implement OpenTelemetryAdapter | 2 |
| 9 | Implement LangfuseAdapter.generate() | 3 |
| 10 | Add trace_id propagation; optional run aggregates | 3 |
| 11 | Cleanup: remove dead code, simplify config | Cleanup |

---

## 8. Reference Files

- **Tracing types/interface:** `agent-eval/sdks/python/agenteval/tracing/` (types.py, base.py, langfuse_adapter.py, opentelemetry_adapter.py)
- **ai-evaluation structure:** `ai-evaluation/src/aieval/`
- **Existing Langfuse:** `ai-evaluation/src/aieval/sinks/langfuse.py`, `adapters/langfuse.py`

---

## 9. Acceptance Criteria (Summary)

- [ ] TracingAdapter interface and types are defined and documented
- [ ] LangfuseTracingAdapter implemented and tested
- [ ] OpenTelemetryAdapter implemented and tested
- [ ] Optional extras work: `pip install aieval[tracing-langfuse]`, `aieval[tracing-otel]`
- [ ] Config supports tracing adapter selection
- [ ] LangfuseAdapter (adapters) can read output from trace
- [ ] Score and Run metadata documented for cost
- [ ] Cleanup audit done; deprecations documented; dead code removed
- [ ] Documentation updated (README, docs/, architecture)
