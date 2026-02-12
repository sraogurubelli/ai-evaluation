# Plan: Eval-first naming and model (eliminate Experiment)

**Status:** For review / implementation.  
**Focus:** DevOps agents + SRE agents; framework-agnostic (LangGraph optional).

---

## 1. Goal

- **Eliminate the word "Experiment"** from the product and docs to avoid confusion with ML experimentation and feature-flag experimentation.
- **Eval-first** naming and model: Eval → Eval Run → Data Sets, Tasks, **Trace**, Scores. (We use **Trace** not “Trail” to avoid confusion with Run and to align with industry: OTel/Langfuse “trace.”)
- **Framework-agnostic:** Support agents built with LangGraph, CrewAI, or any framework; no lock-in.

---

## 2. Naming hierarchy

### Top level: Eval family

| Term | Meaning |
|------|--------|
| **Eval** | Generic: one evaluation definition (what we run, on what, with which scorers). |
| **AgentEval** | Eval of an **agent** (multi-step, tools, memory). **Primary focus** (DevOps/SRE agents). |
| **LLMEval** | Eval of single LLM call(s) / prompt–response. Simpler case. |
| **GenAIEval** | Broader GenAI (agents, LLMs, multimodal). Umbrella when we need it. |

**Implementation:** Eval is the resource. Optional `eval_type` or `kind`: `agent` | `llm` | `genai`. Default and first-class in UX: **AgentEval**.

### Under an Eval: Eval Run and its parts

| Term | Meaning |
|------|--------|
| **Eval Run** (or **Run**) | One execution of an Eval: one (agent version, prompt version) over a Data Set. Produces **Trace** + Scores. |
| **Data Set** | Set of cases (inputs, optional expected) the Run is executed over. Same as today’s “dataset.” |
| **Task** | What we’re evaluating (e.g. “pipeline create”, “incident triage”). Label or first-class field on the Eval. |
| **Trace** | Execution trace of the Run. From BYOT (Langfuse, OTel). One Trace per Run, or one Trace per (Run, dataset item)—TBD. Prefer **Trace** singular in docs (“a Run has a Trace”); per-item traces can be “Trace per item” or left as implementation detail. |
| **Scores** | Per-item and/or run-level scores produced by scorers. |

**Avoid:** “Traces run” as a noun; use “Run produces a Trace” or “Run’s Trace.” Keep **Trace** as the artifact name.

---

## 3. Model (no Experiment)

```
Eval (kind: agent | llm | genai)
├── Task (what we’re evaluating; optional label)
├── Data Set (cases: input + optional expected)
├── Scorers (what we score)
└── Runs
    └── Run
        ├── over Data Set (reference)
        ├── agent version / prompt version (metadata)
        ├── Trace (execution trace from BYOT)
        └── Scores (per item and/or aggregate)
```

- **Eval** = definition (name, task, data set, scorers).
- **Run** = one execution; produces **Trace** + **Scores**.
- **Data Set**, **Task**, **Trace**, **Scores** = first-class concepts in docs and API.

---

## 4. Framework-agnostic

- **Agent Eval** works for agents built with **LangGraph**, CrewAI, custom code, or any framework.
- We do **not** require or depend on LangGraph. We evaluate the agent’s behavior (inputs, outputs, trace), not the framework.
- Docs and positioning: “Agent framework agnostic: evaluate agents built with LangGraph, CrewAI, or any stack.”

---

## 5. Inspiration: Anthropic, OpenAI, Langfuse, and CI/CD practices

- **Anthropic:** Structured evals, clear dimensions (correctness, safety, etc.), methodology and transparency. → We adopt dimensions and “what we measure” clarity.
- **OpenAI:** Evals registry, benchmarks, dataset + run pattern. → We adopt Eval + Run + Data Set as the core model.
- **Langfuse:** Observability first, trace as source of truth, BYOT. → We keep **Trace** (BYOT), optional cost from trace, and “eval on top of your trace.”
- **Continuous evals and canary analysis (CI/CD practice):** Run evals on every change or on a schedule; compare a new agent or prompt version against a baseline before full rollout (canary). We adopt these patterns so teams can gate deployments on eval results (e.g. “run evals in CI” or “canary: new run vs baseline run”).

No vendor names in product copy; we absorb the patterns.

---

## 6. Other moving parts: Prompts (Prompt Registry), LLM versions

These affect how we define a **Run** and how we reproduce or compare runs.

### 6.1 Prompts and Prompt Registry

- **Problem:** A Run is “agent version + prompt version” over a Data Set. Without a clear notion of “prompt version,” we can’t reproduce or compare “same prompt, different model” or “prompt v1 vs v2.”
- **Prompt Registry:** A store of prompts (templates, variables) with versioning. Runs can reference a **prompt id + version** (e.g. `prompt: triage-v2`) so we know exactly what was used. Options:
  - **BYOP (Bring Your Own Prompts):** We don’t build a registry; Run metadata records `prompt_ref` (opaque string or URL). Consumers plug in their own registry (e.g. MLflow Prompt Registry, internal store).
  - **Minimal in-repo registry:** A simple store (e.g. file-based or DB table) of prompt name + version + content. Optional; keeps the OSS minimal.
- **Recommendation (minimal OSS):** Run metadata includes optional `prompt_id` and `prompt_version` (or a single `prompt_ref`). No prompt registry in the open core; document the contract so consumers can plug their own (or add a minimal registry later).

### 6.2 LLM / model versions

- **Problem:** Runs should record which **model** was used (e.g. `gpt-4o`, `claude-3-5-sonnet-20241022`) so we can compare “same prompt, model A vs model B” and reproduce runs.
- **Today:** Adapter and config often imply the model; it may not be first-class in Run metadata.
- **Proposal:** Run metadata (or Eval Run schema) includes optional **model** (or `model_id`): e.g. `model: "gpt-4o"` or `model: "claude-3-5-sonnet-20241022"`. No need to resolve or validate; just store and display. Enables filtering and comparison by model.
- **LLM versioning:** “LLM version” can mean (a) model id (e.g. API model name), (b) model + config (temperature, etc.). For minimal scope, store **model id** in Run metadata; config can stay in adapter/config or be optional metadata.

### 6.3 Summary

| Moving part      | Minimal OSS approach |
|------------------|----------------------|
| **Prompts**      | Run metadata: optional `prompt_id`, `prompt_version`, or `prompt_ref`. No built-in registry; BYOP. |
| **LLM versions** | Run metadata: optional `model` (model id). Enables comparison and reproduction by model. |

These stay **optional** so the core stays minimal; commercial or internal tools can add registry and richer versioning.

---

## 7. What to change (implementation)

### 7.1 Docs and README

- Remove “experiment” from user-facing text. Use **Eval**, **Eval Run**, **Data Set**, **Task**, **Trace**, **Scores**.
- Add one line: “This is **agent evaluation** (Eval, Run, Trace, Scores). Not ML experimentation. Not feature-flag experimentation.”
- Add a short “Concepts” section: Eval, AgentEval, Run, Data Set, Task, Trace, Scores.

### 7.2 API and UI

- Expose **Eval** and **Run** (not Experiment / ExperimentRun) in routes, resource names, and labels.
- Optional: keep internal types as `Experiment` / `ExperimentRun` during transition; map to Eval/Run at API boundary and in responses.

### 7.3 Codebase (later phase)

- Rename `Experiment` → `Eval` (or keep `Experiment` as internal and use “Eval” in API only).
- Rename `ExperimentRun` → `EvalRun` or `Run`.
- Rename `core/experiment.py` → e.g. `core/eval.py` (or keep file name and add Eval as the public concept).
- Update all references (CLI, API, agents, SDK, sinks, DB models) to use Eval/Run terminology in public surface; internal symbols can follow in a second pass.

### 7.4 Trace

- In docs: “**Trace** = execution trace of a Run (from your tracing backend).”
- No new code required for Trace; it’s the existing trace_id + TracingAdapter output. Already `Trace` in `tracing/base.py`.

---

## 8. Acceptance criteria

- [ ] No user-facing use of “Experiment” in README, docs, API resource names, or UI labels.
- [ ] Eval, Run, Data Set, Task, Trace, Scores defined and used consistently in docs.
- [ ] AgentEval (and optionally LLMEval / GenAIEval) documented as eval types; Agent Eval first.
- [ ] Stated as framework-agnostic (LangGraph optional).
- [ ] Internal rename (Experiment → Eval, etc.) either done or scoped as a follow-up task.

---

## 9. Reference

- Competitive analysis: `docs/competitive-analysis.md`
- Strategy (Agent Eval first, dry run, DevOps/SRE): previous discussion in this thread.
- Existing code: `core/experiment.py`, `core/types.py` (ExperimentRun, Score), API models, CLI.
