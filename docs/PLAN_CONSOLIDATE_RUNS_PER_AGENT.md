# Plan addendum: Consolidate runs per agent and show in UI

This extends the eval reports and dashboards plan. Goal: **each time an agent runs an eval, collect the run and report; in the ai-evaluation UI, show runs grouped by agent with summaries and drill-down to reports.**

---

## Agent identity and storage

- **"Agent"** = the evaluation target (e.g. Kubernetes agent, Pipeline agent, Dashboard agent). Each eval run is for one agent.
- **Tagging runs with agent:**
  - **agent_id** is the **unique** identifier for an agent (e.g. `devops-pipeline-agent`, `kubernetes-agent`). CLI and API should send **agent_id** so every run is associated with one agent for grouping.
  - **Option A:** Add optional `agent_id` to the API when creating/running an experiment (e.g. in `POST /experiments` body or task config). Persist on Task and ExperimentRun (DB column or in meta) so runs are queryable by agent_id. Optional `agent_name`/`agent_version` for display.
  - **Option B:** Derive agent from existing data: e.g. `config.dataset.filters.entity_type` or experiment name convention; store in run metadata. Prefer Option A with explicit agent_id for uniqueness.
- **Consumer/CLI:** When calling the API or running via consumer (e.g. run_evals.py), pass **agent_id** (required for grouping) and optionally agent_name/agent_version so every run is uniquely associated with an agent.

---

## Collection when an agent runs

- **API path:** On task completion, when result is written to DB, ensure agent_id (or derived agent) is set so the run appears under that agent.
- **Consumer path:** To collect runs from consumers that run evals locally: (1) Consumer posts run to platform (`POST /agents/{agent_id}/runs` with run payload), or (2) Consumer runs via platform API (create task with agent_id) so platform executes and stores. Prefer (2) for single source of truth.
- **Reports:** For each completed run, generate JUnit/HTML report; store path/URL in run metadata or serve via `GET /runs/{run_id}/report` so the UI can show "View report".

---

## API: list agents and runs per agent

- **GET /agents** — Distinct agents that have at least one run; optional last_run_at, run_count.
- **GET /agents/{agent_id}/runs** — Run summaries for that agent (run_id, created_at, model, summary: total/passed/failed, report link). Query params: limit, offset, optional model.
- **Run detail** — Existing `GET /tasks/{task_id}/result` or add `GET /runs/{run_id}`; optional report URL.
- **Optional:** **GET /agents/{agent_id}/summary** — Aggregate pass rate / trend over last N runs.
- **Optional:** **POST /agents/{agent_id}/runs** — Push run payload from CI or local runs so they appear in "By Agent" and report list.

---

## UI: "By Agent" view and report display

- **Add "By Agent" tab in Gradio (ai-evaluation-ui):**
  - Call `GET /agents`. Display list of agents: agent name, last run time, run count, last run pass/fail summary.
  - User selects an agent → call `GET /agents/{agent_id}/runs`. Show table: run date, model, total/passed/failed, duration; "View" button per run.
  - "View" run → call run detail API; show summary (total/passed/failed) + table of test cases and scores; optional link or embed of HTML report.
- **Flow:** Agent runs (via API with agent_id) → run stored and tagged → appears under that agent in UI → user opens agent → sees list of runs → opens run → sees report/summary. Reports are "collected" by storing runs per agent and exposing them via these endpoints.

---

## Implementation order (add to main plan)

1. **Agent identity** — Add agent_id to API and DB (or derive + store in meta); ensure runs are tagged when stored.
2. **API: agents + runs per agent** — GET /agents, GET /agents/{agent_id}/runs, run detail; optional POST for push.
3. **Gradio "By Agent"** — New tab: list agents, runs per agent, view run report/summary so consolidated reports show in ai-evaluation-ui.

See main plan for JUnit/HTML sinks, run list/summary API, and "View results" enhancement.
