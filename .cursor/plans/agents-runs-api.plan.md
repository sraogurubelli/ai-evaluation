# Plan: Agents and runs API (consolidation per agent)

## Overview

Platform APIs and consumer tooling to consolidate evaluation runs by agent: list agents, list runs per agent, view run details, HTML/JUnit reports, and push runs from CI/consumers.

## Decisions

- **Agent identity:** `agent_id` is the unique key for grouping; optional `agent_name`, `agent_version` for display.
- **Storage:** In-memory `_pushed_runs` for consumer-pushed runs; task-derived runs from completed experiment tasks.
- **Endpoints:** `GET /agents`, `GET /agents/{id}/runs`, `GET /runs/{id}`, `GET /runs/{id}/report`, `POST /agents/{id}/runs`.

## Implemented

- CLI: `samples_sdk/consumers/devops/run_evals.py` (agent_id, JUnit/HTML sinks, streaming).
- Sinks: `src/aieval/sinks/junit.py`, `src/aieval/sinks/html_report.py`.
- API: agent/runs routes in `src/aieval/api/app.py`.
- UI: "By Agent" tab in Gradio (`src/aieval/ui/gradio_app.py`).
- Tests: `tests/api/test_agents_runs.py` (integration); API test fixes in conftest, health, dataset, experiments.

## Status

Done. See docs/PLAN_CONSOLIDATE_RUNS_PER_AGENT.md for full design.
