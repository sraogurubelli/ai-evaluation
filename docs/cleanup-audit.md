# Cleanup audit

**Purpose:** List CLI commands, config options, adapters, sinks, scorers, and migrations with status. Use for deprecation and cleanup decisions. See [.cursor/plans/ownership-licensing-cleanup.plan.md](../.cursor/plans/ownership-licensing-cleanup.plan.md) for the full cleanup plan.

---

## 1. CLI commands

| Command | Location | Status | Notes |
|---------|----------|--------|-------|
| `run` | `src/aieval/cli/main.py` | **Implemented** | Runs experiment from YAML config; supports dataset (jsonl, index_csv), adapters (http, ml_infra), scorers, sinks (stdout, csv, json, langfuse), models, concurrency. |
| `compare` | `src/aieval/cli/main.py` | **Not implemented** | Raises `NotImplementedError`; requires run storage. Mark as not implemented in docs; consider for future or remove. |

**DevOps consumer (separate entry point):** `samples_sdk/consumers/devops/run_evals.py` — implements CLI for agent evals (agent_id, JUnit/HTML sinks, streaming). **In use.**

---

## 2. Config options (YAML / config.yml)

| Section | Options | Used by | Status |
|---------|---------|--------|--------|
| `experiment` | name, description | CLI run, API | **Used** |
| `dataset` | type, path, index_file, base_dir, filters, offline, actual_suffix | CLI run, API | **Used** |
| `adapter` | type, base_url, auth_token, context_*, endpoint_mapping, etc. | CLI run, tasks/manager | **Used** |
| `models` | list of model names | CLI run | **Used** |
| `scorers` | type, version, model, rubric, api_key, validation_func, entity_type | CLI run, API | **Used** |
| `execution` | concurrency_limit, sample_size | CLI run | **Used** (sample_size optional) |
| `output.sinks` | type, path, project | CLI run | **Used** |

**Config file:** `config.yml` — ML Infra example; all options above are used. No unused top-level keys found.

**Application settings (env):** `src/aieval/config/settings.py` — Database, Server, Logging, Temporal, Langfuse, Security, Monitoring. All used by API/server. Keep.

---

## 3. Adapters

| Adapter | Location | Status | Notes |
|---------|----------|--------|-------|
| **HTTPAdapter** | `adapters/http.py` | **Implemented** | Primary adapter for REST APIs. |
| **SSEStreamingAdapter** | `adapters/sse_streaming.py` | **Implemented** | Used for streaming; factory exists. |
| **LangfuseAdapter** | `adapters/langfuse.py` | **Placeholder** | `generate()` raises `NotImplementedError`. To be completed (see tracing plan). |
| **ml_infra** (via HTTPAdapter) | CLI + tasks/manager | **Deprecated** | Emits DeprecationWarning; use `http` with ml-infra config. |

**Factory:** `adapters/factory.py` — create_http_adapter, create_sse_streaming_adapter, create_langfuse_adapter, create_ml_infra_adapter. Used by API/AdapterAgent. Keep.

---

## 4. Sinks

| Sink | Location | Status | Used by |
|------|----------|--------|--------|
| **StdoutSink** | `sinks/stdout.py` | **Implemented** | CLI run |
| **CSVSink** | `sinks/csv.py` | **Implemented** | CLI run |
| **JSONSink** | `sinks/json.py` | **Implemented** | CLI run |
| **LangfuseSink** | `sinks/langfuse.py` | **Implemented** | CLI run (optional) |
| **JUnitSink** | `sinks/junit.py` | **Implemented** | DevOps consumer (run_evals.py) |
| **HTMLReportSink** | `sinks/html_report.py` | **Implemented** | DevOps consumer |

**Note:** Main CLI (`aieval run -c config.yml`) does not wire JUnit/HTML sinks from config; they are used by the DevOps consumer. To expose in main CLI, add sink types to `_create_sinks()` in `cli/main.py` (optional enhancement).

---

## 5. Scorers

| Scorer | Location | Status | Used by |
|--------|----------|--------|--------|
| **DeepDiffScorer** | `scorers/deep_diff.py` | **Implemented** | CLI, API |
| **SchemaValidationScorer** | `scorers/schema_validation.py` | **Implemented** | CLI, API |
| **DashboardQualityScorer** | `scorers/dashboard.py` | **Implemented** | CLI, API |
| **KnowledgeGraphQualityScorer** | `scorers/knowledge_graph.py` | **Implemented** | CLI, API |
| **LLMJudgeScorer** | `scorers/llm_judge.py` | **Implemented** | CLI, API (optional) |
| **Guardrails** (e.g. PII, toxicity) | `scorers/guardrails/` | **Implemented** | Available for use |
| **Autoevals, metrics, enriched** | `scorers/` | **Implemented** | SDK/API as needed |

All listed scorers are implemented and used or available. No dead scorer code identified.

---

## 6. Dataset types (CLI)

| Type | Status | Notes |
|------|--------|-------|
| **jsonl** | **Implemented** | Loads from path. |
| **index_csv** | **Implemented** | Loads from index_file + base_dir + filters. |
| **function** | **Not implemented** | Raises `NotImplementedError` in `_load_dataset()`. Mark as not implemented in docs. |

---

## 7. Migrations

| Path | Purpose | Status |
|------|---------|--------|
| `migrations/ml_infra_evals/` | Migration scripts for ml_infra evals (migration_script.py, validate_migration.py) | **Review** — Keep if ml_infra users need one-off migration; else document as optional/legacy. |
| `alembic/` | DB schema migrations (Alembic) | **Keep** — Used for app database. |

---

## 8. Summary: deprecations and removals

- **Mark as not implemented (docs):** CLI `compare`; dataset type `function`.
- **Already deprecated:** `adapter.type: ml_infra` — keep warning; document in custom-adapters.md.
- **No immediate removals** — No dead adapters/sinks/scorers; config and settings are in use. Removals can follow after deprecation period if any feature is phased out.

---

## 9. Items to keep (per plan)

- Core: Experiment, Dataset, Scorers.
- HTTPAdapter, LangfuseSink; LangfuseAdapter (complete in tracing phase).
- Score with trace_id, observation_id.
- OpenTelemetry monitoring (ai-evaluation service).
- API, CLI (implemented parts).
- DevOps consumer.
- Sinks: CSV, JSON, stdout, JUnit, HTML report, Langfuse.
