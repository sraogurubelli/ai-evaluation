# Temporal Integration Guide

## Overview

AI Evolution integrates with Temporal for reliable, long-running workflow orchestration. Temporal provides:

- **Durable Execution**: Workflows survive crashes and restarts
- **Automatic Retries**: Built-in retry logic for failed activities
- **Workflow History**: Complete audit trail of execution
- **Distributed Execution**: Scale workers across multiple machines
- **State Management**: Persistent workflow state

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI / CLI                                         │
│  - Create experiment tasks                              │
│  - Query workflow status                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Temporal Workflows                                     │
│  - ExperimentWorkflow (orchestrates execution)          │
│  - MultiModelWorkflow (runs multiple models)            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Temporal Activities                                    │
│  - LoadDatasetActivity                                  │
│  - GenerateOutputActivity                               │
│  - ScoreOutputActivity                                  │
│  - EmitResultsActivity                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Temporal Workers                                       │
│  - Execute workflows and activities                     │
│  - Handle retries and failures                          │
└─────────────────────────────────────────────────────────┘
```

## Benefits

### 1. **Reliability**
- Workflows automatically resume after crashes
- Activities retry on transient failures
- No data loss during execution

### 2. **Observability**
- Complete workflow history
- Temporal UI for monitoring
- Detailed execution logs

### 3. **Scalability**
- Distribute workers across machines
- Parallel activity execution
- Efficient resource utilization

### 4. **Long-Running Support**
- Workflows can run for days/weeks
- Checkpoint state automatically
- Resume from last checkpoint

## Usage

### Starting Temporal Server

```bash
# Using Docker (recommended)
docker run -p 7233:7233 temporalio/auto-setup:latest

# Or install locally
temporal server start-dev
```

### Starting Workers

```bash
# Start Temporal worker
python -m ai_evolution.workflows.worker

# Or use task command
task temporal-worker
```

### Running Experiments

```python
from ai_evolution.workflows.client import start_experiment_workflow

# Start workflow
workflow_id = await start_experiment_workflow(
    experiment_name="my_experiment",
    config={...},
)

# Query status
status = await get_workflow_status(workflow_id)
```

## Configuration

### Environment Variables

```bash
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=ai-evolution
```

### Temporal Server Options

- **Local Development**: `temporal server start-dev`
- **Docker**: `docker run temporalio/auto-setup:latest`
- **Temporal Cloud**: Use Temporal Cloud credentials

## Workflow Patterns

### 1. Single Model Experiment

```python
@workflow.defn
class ExperimentWorkflow:
    @workflow.run
    async def run(self, config: dict) -> ExperimentRun:
        # Load dataset
        dataset = await workflow.execute_activity(
            load_dataset_activity,
            config["dataset"],
        )
        
        # Run experiment
        result = await workflow.execute_activity(
            run_experiment_activity,
            dataset, config,
        )
        
        return result
```

### 2. Multi-Model Experiment

```python
@workflow.defn
class MultiModelWorkflow:
    @workflow.run
    async def run(self, config: dict) -> list[ExperimentRun]:
        models = config.get("models", [])
        results = []
        
        for model in models:
            result = await workflow.execute_activity(
                run_experiment_activity,
                config, model,
            )
            results.append(result)
        
        return results
```

### 3. Parallel Scoring

```python
# Score multiple items in parallel
scoring_tasks = [
    workflow.execute_activity(
        score_item_activity,
        item, scorers,
    )
    for item in dataset
]
scores = await asyncio.gather(*scoring_tasks)
```

## Retry Configuration

```python
from temporalio.common import RetryPolicy

retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=5,
)
```

## Monitoring

### Temporal UI

Access Temporal UI at `http://localhost:8088` (default)

- View running workflows
- Inspect workflow history
- Debug failed workflows
- Monitor activity execution

### Integration with Langfuse

Workflow execution can be traced in Langfuse:
- Each activity creates a trace
- Workflow ID links all traces
- Complete observability chain

## Migration Path

1. **Phase 1**: Add Temporal alongside existing system
2. **Phase 2**: Migrate long-running experiments to Temporal
3. **Phase 3**: Use Temporal for all experiment execution
4. **Phase 4**: Remove old task manager (optional)

## Best Practices

1. **Keep Activities Idempotent**: Activities should be safe to retry
2. **Use Workflow Time**: Use `workflow.now()` instead of `datetime.now()`
3. **Avoid Non-Deterministic Code**: No random, file I/O, or network in workflows
4. **Keep Activities Focused**: One activity = one operation
5. **Handle Failures Gracefully**: Use try/except in activities
