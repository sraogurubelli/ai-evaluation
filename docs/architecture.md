# Architecture

## Overview

AI Evolution is a unified evaluation and experimentation system designed for testing and improving AI systems. It's open source, self-hostable, and production-ready.

## Core Components

### 1. Experiment System

The `Experiment` class is the central orchestrator:

- **Dataset**: Collection of test cases (inputs + optional expected outputs)
- **Scorers**: List of evaluation functions to apply
- **Runs**: Track multiple executions over time
- **Comparison**: Compare runs to identify improvements/regressions

### 2. Dataset System

Supports multiple formats:

- **JSONL**: Simple line-delimited JSON (from ai-evals)
- **Index CSV**: File-based structure (from ml-infra/evals)
- **Function-based**: Dynamic generation (Braintrust pattern)

### 3. Scorer System

Unified abstraction for evaluation:

- **Code-based**: DeepDiff, schema validation, string matching
- **LLM-as-judge**: Rubric-based evaluation
- **Entity-specific**: Dashboard quality, KG quality

### 4. Adapter System

Interface for different AI systems:

- **HTTPAdapter**: Generic HTTP/REST adapter (recommended, configurable for any API)
- **HTTPAdapter**: Generic HTTP adapter that can be configured for any REST API
- **Extensible**: Easy to add new adapters by implementing the Adapter interface

### 5. Sink System

Output handlers:

- **CSV**: For ml-infra compatibility
- **JSON**: Structured output
- **Langfuse**: Optional observability integration
- **Stdout**: Console output

## Data Flow

```
Dataset → Experiment → Adapter → Generated Output
                              ↓
                         Scorers → Scores
                              ↓
                            Sinks → Results
```

## Design Principles

1. **Gradual Migration**: Support both old and new formats
2. **Langfuse Optional**: Can use built-in or existing Langfuse instance
3. **Self-Hosted First**: Designed for self-hosting
4. **Extensible**: Easy to add scorers, adapters, sinks

## Component Relationships

```
Experiment
  ├── Dataset (list[DatasetItem])
  ├── Scorers (list[Scorer])
  └── Runs (list[ExperimentRun])
        └── Scores (list[Score])
              └── Sinks (emit results)
```

## Extension Points

- **Custom Scorers**: Implement `Scorer` interface
- **Custom Adapters**: Implement `Adapter` interface
- **Custom Sinks**: Implement `Sink` interface
- **Custom Datasets**: Use `FunctionDataset` or implement loader
