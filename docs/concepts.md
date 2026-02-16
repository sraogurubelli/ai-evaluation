# Concepts

This project is **agent evaluation**: you define evals, run them over data sets, and get EvalResults with scores. The core concepts are:

**This is agent evaluation. Not ML experimentation. Not feature-flag experimentation.**

---

## Eval

An **Eval** (evaluation) is the definition of what you want to measure: a name, a **Task** (what you're evaluating), a **Data Set** (the cases), and one or more **Scorers** (how to score each case). In the SDK it is represented by the `Experiment` class.

## EvalResult

An **EvalResult** is the result of executing an Eval. You run an Eval (e.g. over a data set, with a given adapter and model) and get back an EvalResult that contains **Scores** for each case, plus optional metadata (model, trace IDs, cost). Compare EvalResults to check regressions (e.g. prompt v1 vs v2, model A vs B).

## Data Set

A **Data Set** is the set of inputs (and optionally expected outputs) you run the Eval over. Load from JSONL, index CSV, or provide via a function. Each item is a **Task** (one case).

## Task

A **Task** is a single case: one input (and optionally expected output) from the Data Set. The adapter generates output for the task; scorers produce scores for that task.

## Trace

A **Trace** is the execution trace of the agent (or model) for a task—steps, tokens, latency, cost. This project does not build a tracing product; you **bring your own trace** (BYOT). Use a TracingAdapter (e.g. Langfuse, OpenTelemetry) to read traces and attach trace IDs and cost to scores. See [tracing](tracing.md).

## Scores

**Scores** are the results of running Scorers on the adapter output for each task. An EvalResult contains scores per task (and optionally aggregate metrics). Scores can carry a `trace_id` when BYOT tracing is configured.

---

## AgentEval

When the Eval is focused on evaluating **agents** (e.g. DevOps agents, SRE agents), we sometimes call it an **AgentEval**. The same concepts apply: Eval, EvalResult, Data Set, Task, Trace, Scores.
