# Architecture

Unified evaluation system: datasets, scorers, adapters, sinks. The last two sections define **minimal open source scope** and **differentiators** for a future hosted offering (targeting smaller AI companies).

## Core flow

```
Data Set → Eval → Adapter → Generated output
                                ↓
                           Scorers → Scores
                                ↓
                             Sinks → Results
```

## Components

- **Eval:** Orchestrates dataset + scorers + runs. Compare runs for regressions.
- **Dataset:** JSONL, index CSV, or function-based. Load via `load_jsonl_dataset` or DevOps consumer.
- **Scorers:** DeepDiff, schema validation, LLM-as-judge, entity-specific. Implement `Scorer` for custom.
- **Adapters:** `HTTPAdapter` for any REST API. Implement `Adapter` for custom. See [custom-adapters](custom-adapters.md).
- **Sinks:** CSV, JSON, stdout, Langfuse. Implement `Sink` for custom.

## Tracing integration (BYOT)

- **TracingAdapter** (in `aieval.tracing`): read traces and cost from the user's tracing system (Langfuse, OpenTelemetry/Jaeger). Optional; install `aieval[tracing-langfuse]` or `aieval[tracing-otel]`.
- **Score** and **Run** metadata can carry cost/token data; see [tracing](tracing.md).

## Extension points

- **Custom scorers:** Implement `Scorer` interface.
- **Custom adapters:** Implement `Adapter` or extend `HTTPAdapter`.
- **Custom tracing adapters:** Implement `TracingAdapter` in `aieval.tracing.base`.
- **Custom sinks:** Implement `Sink` interface.
- **Custom datasets:** Use `FunctionDataset` or add loader.

## Principles

Gradual migration (old + new formats), Langfuse optional, self-hosted first, extensible. Core is domain-agnostic; domain-specific logic lives in scorers, adapters, datasets, and sinks.

---

## Minimal open source scope

The open source project is a **minimal eval kernel**: enough to run evals, compare runs, and extend. Naming aligns with Eval-first (see [.cursor/plans/eval-first-naming-and-model.plan.md](../.cursor/plans/eval-first-naming-and-model.plan.md)): **Eval**, **Run**, **Data Set**, **Task**, **Trace**, **Scores**.

### In scope (minimal OSS)

| Layer | What's included |
|-------|------------------|
| **Concepts** | Eval (definition), Run (one execution), Data Set (cases), Task (what we're evaluating), Trace (execution trace from BYOT), Scores. |
| **Runner** | Run an Eval over a Data Set → produce Runs with Scores; optional Trace via TracingAdapter. |
| **Adapters** | Small set (e.g. HTTP, Langfuse for reading trace output). Extension point for custom. |
| **Scorers** | Base interface + a few concrete (e.g. DeepDiff, one LLM-judge path). Extension point for custom. |
| **Data Set** | Load from JSONL, index CSV (or one primary format). Extension point for custom loaders. |
| **Tracing** | BYOT only: Trace from TracingAdapter (Langfuse/OTel); trace_id on Score. No tracing product. |
| **API** | Small REST API for Eval, Run, Data Set, Scores (or CLI-only). |
| **Output** | Sinks: CSV, JSON, stdout, Langfuse. No built-in hosted UI. |

### Out of scope (minimal OSS)

- No built-in prompt registry (BYOP; Run metadata can reference prompt_id / prompt_version).
- No continuous evals or canary automation in core (triggering and gating are external or future).
- No team/org/SSO, no managed CI/CD integration, no hosted service.
- No enterprise features (audit, compliance, SLA) in the open repo.

### Boundary

A single team can **self-host** this repo and: define Evals, run over Data Sets, get Runs with Scores and optional Trace, compare runs (e.g. prompt v1 vs v2, model A vs B). Everything beyond that (scheduling, gating, hosted UX, team features) is **outside the minimal kernel** and can be built on top or offered as a separate product.

### Extensions (available but not minimal)

The following are **extensions** to the minimal kernel. They are available in the codebase but are not part of the core minimal scope:

| Category | Extension | Notes |
|----------|-----------|-------|
| **Adapters** | `SSEStreamingAdapter` | Streaming support; use `HTTPAdapter` for basic REST APIs |
| **Scorers** | `DashboardQualityScorer`, `KnowledgeGraphQualityScorer` | Entity-specific scorers for domain-specific use cases |
| **Scorers** | `EnrichedOutputScorer`, `LatencyScorer`, `ToolCallScorer`, `TokenUsageScorer` | Metrics-focused scorers |
| **Scorers** | Autoevals-style scorers (`FactualityScorer`, `HelpfulnessScorer`, etc.) | Requires optional `aieval[autoevals]` dependency |
| **Scorers** | Guardrail scorers (`HallucinationScorer`, `PromptInjectionScorer`, etc.) | Requires optional `aieval[guardrails]` dependency |
| **Data Sets** | `FunctionDataset` | Function-based datasets (not implemented in CLI; use programmatically) |
| **Sinks** | `JUnitSink`, `HTMLReportSink` | Specialized output formats (used by DevOps consumer) |

**Note:** The minimal kernel focuses on HTTP adapters, DeepDiff/LLM-judge scorers, JSONL/index-CSV datasets, and CSV/JSON/stdout/Langfuse sinks. Extensions are available for teams with specific needs but are not required for the core eval workflow.

---

## Differentiators (target later)

These are **not** in the minimal open source. They are potential differentiators for a **hosted or commercial** offering, aimed at **smaller AI companies** who are fine with a hosted solution and don’t need to self-host.

| Differentiator | Description |
|----------------|-------------|
| **Hosted platform** | Managed eval service: no self-host, smaller companies can sign up and run evals in the cloud. |
| **Continuous evals** | Run evals on every commit or on a schedule; results and history in one place. |
| **Canary analysis** | Compare a candidate Run to a baseline Run (e.g. new prompt vs old); gate rollout on score/regression thresholds. |
| **Prompt registry** | Versioned prompt store; Runs reference prompt id + version for reproducibility and comparison. |
| **LLM version tracking** | Run metadata + UI to filter and compare by model; “same prompt, model A vs B.” |
| **CI/CD integration** | Turnkey (e.g. GitHub Action) to run evals in CI and block merge on regressions. |
| **Team and collaboration** | Orgs, workspaces, shared Data Sets and Evals (optional; may stay minimal for SMB). |
| **DevOps/SRE focus** | Templates, dry-run semantics, and docs for agent evals (pipeline, incident, IaC). |

### Target audience for hosted

- **Smaller and new AI companies** who prefer not to operate the open source stack themselves.
- **Single team or small org** that wants evals + optional canary/continuous evals without enterprise features (no requirement for heavy compliance or SSO in v1).

The open source kernel remains **independent**: no dependency on a commercial product; the hosted offering, if built, would consume or extend the same concepts (Eval, Run, Data Set, Task, Trace, Scores).
