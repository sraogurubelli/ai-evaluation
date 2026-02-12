---
name: ""
overview: ""
todos: []
isProject: false
---

# Plan: Open source minimal scope and cleanup (eliminate Experiment)

**Status:** For review / implementation.
**Assumption:** ai-evaluation is an **independent open source project**.

---

## 1. Positioning

- **ai-evaluation** = open source project: minimal eval kernel for **Eval**, **Run**, **Data Set**, **Task**, **Trace**, **Scores**.
- **Target:** DevOps agents, SRE agents; framework-agnostic. Teams may use it as inspiration or as a dependency to build their own internal eval tools.

---

## 2. Minimal scope (what the OSS delivers)

Keep the surface **minimal** so the project is easy to understand, extend, and use as a reference.

| Area | In scope (minimal) | Out of scope / trim |
|------|--------------------|----------------------|
| **Core model** | Eval, Run, Data Set, Task, Trace, Scores (no “Experiment”) | Legacy Experiment/ExperimentRun naming; redundant abstractions |
| **Runner** | Run an Eval over a Data Set → Runs, Scores, optional Trace (BYOT) | Heavy orchestration; vendor-specific runners |
| **Adapters** | One or two (e.g. HTTP, Langfuse for trace read) | Proliferation of adapters in core |
| **Scorers** | Base interface + 1–2 concrete (e.g. DeepDiff, one LLM judge path) | Many specialized scorers in core (can be examples or separate) |
| **Data Set** | Load from JSONL, index CSV (or one format) | Every possible format in core |
| **Tracing** | BYOT: Trace from TracingAdapter (Langfuse/OTel); trace_id on Score | Building a tracing product |
| **API** | Small REST API for Eval, Run, Data Set, Scores (or CLI-only) | Full enterprise API surface |
| **UI** | Optional minimal UI or CLI-only | Full product UI |
| **Docs** | README, concepts (Eval, Run, Data Set, Task, Trace, Scores), one “not ML / not feature-flag” line | Large doc set |

**Principle:** A single team can run Evals and compare Runs (agent/prompt versions) with Data Sets, Trace, and Scores using only this repo. No vendor-specific code or branding in the open source codebase.

---

## 3. Cleanup: eliminate Experiment

- **Remove** the word “Experiment” from all **user-facing** surfaces: README, docs, API resource names, API response labels, CLI output, UI labels.
- **Rename** to Eval/Run model:
- **Experiment** → **Eval** (the definition: name, task, data set, scorers).
- **ExperimentRun** → **Run** (or **EvalRun**) (one execution of an Eval).
- **Codebase:** Either rename types/files (e.g. `Experiment` → `Eval`, `ExperimentRun` → `Run`, `core/experiment.py` → `core/eval.py`) or keep internal names and **map at API/docs boundary** (recommended for first phase: map at boundary; internal rename in a later phase).
- **Glossary:** Add a short “Concepts” section: Eval, AgentEval, Run, Data Set, Task, Trace, Scores. State clearly: “This is agent evaluation. Not ML experimentation. Not feature-flag experimentation.”

---

## 4. Implementation checklist

### Phase 1: Docs and user-facing naming (no code rename yet)

- [ ] README: Remove “experiment”; use Eval, Run, Data Set, Task, Trace, Scores. Add one line: “Agent evaluation only. Not ML experiments. Not feature-flag experiments.”
- [ ] Add `docs/concepts.md` (or equivalent): Eval, AgentEval, Run, Data Set, Task, Trace, Scores.
- [ ] API: Expose resources as Eval / Run (and Data Set, Scores) in routes and response keys; keep internal types as-is if desired.
- [ ] CLI: Use “eval” and “run” in commands and output (e.g. `aieval eval run`, “Eval run completed”).

### Phase 2: Minimal scope trim (optional)

- [ ] Identify and trim or move out of core: redundant adapters, scorers, or formats that don’t fit “minimal.”
- [ ] Ensure one clear path: “Run an Eval over a Data Set → get Runs with Scores (and Trace if BYOT configured).”

### Phase 3: Internal rename (optional, later)

- [ ] Rename `Experiment` → `Eval`, `ExperimentRun` → `Run` (or `EvalRun`) in code and DB.
- [ ] Rename `core/experiment.py` → `core/eval.py` (or keep filename and export Eval).
- [ ] Update all references across repo; preserve API compatibility with aliases if needed.

---

## 5. Acceptance criteria

- [ ] No user-facing “Experiment” in README, docs, API, CLI, UI.
- [ ] Eval, Run, Data Set, Task, Trace, Scores are the only first-class concepts in docs and API.
- [ ] Repo is self-contained and minimal; no vendor-specific code or branding.
- [ ] “Independent open source project” is stated in README or CONTRIBUTING (one sentence).

---

## 6. Reference

- [eval-first-naming-and-model.plan.md](eval-first-naming-and-model.plan.md) — Naming hierarchy and model.
- [competitive-analysis.md](../../docs/competitive-analysis.md) — Context vs Braintrust, Langfuse, etc.