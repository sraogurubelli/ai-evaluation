# Cursor plans

This folder holds **plan documents** for the project: product decisions, naming, architecture, and implementation outlines. Plans are the source of truth for "what we decided and why." **Team should review plans here before starting implementation.**

## Conventions

- **One plan per initiative or decision** — Keep each file focused so plans are easy to find and update.
- **Naming** — Use lowercase slugs with hyphens: `feature-name.plan.md` or `topic.plan.md`.
- **Format** — Markdown with a clear title, short overview, decisions/todos, and acceptance criteria as needed.

## Plans index

| Plan | Purpose |
|------|---------|
| [product-naming.plan.md](product-naming.plan.md) | Product and *IQ family naming (SynteraIQ, Agent*IQ, etc.). |
| [agents-runs-api.plan.md](agents-runs-api.plan.md) | API and CLI for agent runs, consolidation, reports (implemented). |
| [tracing-and-cost-improvements.plan.md](tracing-and-cost-improvements.plan.md) | **For review:** TracingAdapter, cost extraction, Langfuse/OTel phases 0–3. |
| [ownership-licensing-cleanup.plan.md](ownership-licensing-cleanup.plan.md) | **For review:** Ownership/licensing, cleanup audit, deprecations, hardening. |
| [eval-first-naming-and-model.plan.md](eval-first-naming-and-model.plan.md) | **Eval-first:** Eliminate Experiment; Eval, AgentEval, Run, Data Set, Task, Trace, Scores; framework-agnostic. |
| [open-source-minimal-and-cleanup.plan.md](open-source-minimal-and-cleanup.plan.md) | **OSS minimal:** ai-evaluation as independent OSS; minimal scope; eliminate Experiment; no vendor names. |

## Source design docs (reference)

- `AI_EVALUATION_IMPROVEMENTS_DESIGN.md` — Design for tracing, cost, BYOT.
- `AI_EVALUATION_IMPLEMENTATION_PLAN.md` — Phased implementation, cleanup, acceptance criteria.

Plans in this folder distill those docs into review-ready Cursor plans. Version with the repo so the team and Cursor share the same context.
