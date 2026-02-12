---
name: ""
overview: ""
todos: []
isProject: false
---

# Plan: Ownership, licensing, and cleanup

**Source:** [AI_EVALUATION_IMPLEMENTATION_PLAN.md](../../AI_EVALUATION_IMPLEMENTATION_PLAN.md)
**Status:** For team review before implementation.

---

## 1. Overview

Confirm ownership and licensing for the ai-evaluation repo; run an audit and cleanup (deprecations, dead code, config simplification) so the codebase is clear before adding tracing and cost work.

---

## 2. Ownership and licensing (decisions for review)

| Decision | Choice | Action |
|----------|--------|--------|
| **Copyright** | Srinivasa Rao Gurubelli (VP of Engineering & Fellow); project maintainer | Document in README and LICENSE. |
| **License** | MIT (already in place) | Keep; ensure LICENSE file is correct. |
| **CLA** | No corporate CLA; use project-specific contributor terms if any, or DCO/inbound=license | Document in CONTRIBUTING.md. |
| **Contributors** | Open: contributors welcome from anywhere under the same terms | Document in CONTRIBUTING.md. |

**Deliverables:** Update LICENSE + README with copyright holder: Srinivasa Rao Gurubelli (VP of Engineering & Fellow); add or update CONTRIBUTING.md (how to contribute, that contributors are welcome from anywhere).

**Done:** LICENSE, README, and CONTRIBUTING.md updated.

---

## 3. Cleanup plan (order of operations)

### 3.1 Audit (do first)

Create a list of:

- [x] All CLI commands and their usage (implemented, placeholder, unused).
- [x] All config options and whether they are used.
- [x] All adapters, sinks, scorers and their status.
- [x] Migration scripts and whether they are still needed.

**Output:** Audit document — [docs/cleanup-audit.md](../../docs/cleanup-audit.md) (done).

### 3.2 Deprecations

- [x] Mark unimplemented CLI features (e.g. `compare`, `function` dataset) as deprecated or "not implemented" in docs.
- [x] Add deprecation warnings for any APIs/config being phased out (ml_infra already has DeprecationWarning).
- [ ] Set removal timeline (e.g. next major version) if applicable — optional.

### 3.3 Removals (after deprecation period)

- [ ] Remove dead code identified in audit.
- [ ] Remove unused config options.
- [ ] Consolidate duplicate logic where safe.

### 3.4 Simplification

- [ ] Reduce config to minimal set: dataset, scorers, adapters, sinks, tracing.
- [ ] Remove or document experimental/unfinished features that add confusion.
- [ ] Update examples to use only supported features.

### 3.5 Items to keep

- Core: Experiment, Dataset, Scorers.
- HTTPAdapter, LangfuseSink.
- Score with trace_id, observation_id.
- OpenTelemetry monitoring (for ai-evaluation service).
- API, CLI (implemented parts).
- DevOps consumer (if used).
- Existing sinks: CSV, JSON, stdout, JUnit, HTML report.

---

## 4. Hardening (quality, docs, deps)

### 4.1 Code quality

- [ ] Type hints on new tracing code.
- [ ] Unit tests for TracingAdapter implementations.
- [ ] Integration test with mock Langfuse/OTel responses (or testcontainers if feasible).
- [ ] Lint and format (ruff, black, mypy per project norms).

### 4.2 Documentation

- [ ] README: mention tracing, cost extraction, optional extras.
- [ ] `docs/tracing.md`: full tracing design and usage (created in Phase 0).
- [ ] `docs/architecture.md`: update with tracing layer.
- [ ] API docs: document new modules and public functions.

### 4.3 Dependencies

- [ ] Core `aieval` has minimal deps; tracing is optional.
- [ ] `langfuse` only for `aieval[tracing-langfuse]`.
- [ ] `httpx` (or similar) only for `aieval[tracing-otel]`.

### 4.4 Configuration

- [ ] Document `tracing.adapter`, `tracing.langfuse.*`, `tracing.opentelemetry.*`.
- [ ] Use env vars for secrets (LANGFUSE_SECRET_KEY, etc.); `.env.example` updated.

---

## 5. Implementation order (high level)

| # | Task | When |
|---|------|------|
| 1 | Confirm ownership; update LICENSE, README, CONTRIBUTING | Pre (before Phase 0) |
| 2 | Audit: CLI, config, adapters, sinks, migrations | Cleanup |
| 3 | Document deprecations; add warnings if needed | Cleanup |
| 4 | Tracing phases 0–3 (see tracing-and-cost-improvements.plan.md) | Phases 0–3 |
| 5 | Remove dead code; simplify config (after deprecation) | Cleanup |
| 6 | Hardening: tests, docs, deps | Ongoing |

---

## 6. Acceptance criteria

- [ ] Ownership and licensing documented; CONTRIBUTING.md present.
- [ ] Audit completed and reviewed; deprecations documented.
- [ ] Dead code removed; config simplified per audit.
- [ ] New code has tests and docs; optional extras work as specified.