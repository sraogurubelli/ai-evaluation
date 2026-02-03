# Architecture

Unified evaluation system: datasets, scorers, adapters, sinks.

## Core flow

```
Dataset → Experiment → Adapter → Generated output
                                    ↓
                               Scorers → Scores
                                    ↓
                                 Sinks → Results
```

## Components

- **Experiment:** Orchestrates dataset + scorers + runs. Compare runs for regressions.
- **Dataset:** JSONL, index CSV, or function-based. Load via `load_jsonl_dataset` or DevOps consumer.
- **Scorers:** DeepDiff, schema validation, LLM-as-judge, entity-specific. Implement `Scorer` for custom.
- **Adapters:** `HTTPAdapter` for any REST API. Implement `Adapter` for custom. See [custom-adapters](custom-adapters.md).
- **Sinks:** CSV, JSON, stdout, Langfuse. Implement `Sink` for custom.

## Extension points

- **Custom scorers:** Implement `Scorer` interface.
- **Custom adapters:** Implement `Adapter` or extend `HTTPAdapter`.
- **Custom sinks:** Implement `Sink` interface.
- **Custom datasets:** Use `FunctionDataset` or add loader.

## Principles

Gradual migration (old + new formats), Langfuse optional, self-hosted first, extensible. Core is domain-agnostic; domain-specific logic lives in scorers, adapters, datasets, and sinks.
