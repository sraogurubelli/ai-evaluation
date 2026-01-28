# API Documentation

## Overview

AI Evolution provides a REST API for managing experiments and tasks. The API follows an agent-based architecture where each evaluation capability is handled by a dedicated agent with its own endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production, add authentication middleware.

## Endpoints

### Health Check

**GET** `/health`

Check API health and get task statistics.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "tasks": {
    "pending": 2,
    "running": 1,
    "completed": 10,
    "failed": 0,
    "cancelled": 0
  }
}
```

### Create Experiment

**POST** `/experiments`

Create and optionally run an experiment.

**Request Body:**
```json
{
  "experiment_name": "pipeline_creation_benchmark",
  "config": {
    "dataset": {
      "type": "index_csv",
      "index_file": "benchmarks/datasets/index.csv",
      "base_dir": "benchmarks/datasets",
      "filters": {
        "entity_type": "pipeline",
        "operation_type": "create"
      }
    },
    "adapter": {
      "type": "ml_infra",
      "base_url": "http://localhost:8000",
      "auth_token": "your-token"
    },
    "models": ["claude-3-7-sonnet-20250219"],
    "scorers": [
      {"type": "deep_diff", "version": "v3"}
    ],
    "execution": {
      "concurrency_limit": 5
    }
  },
  "run_async": true
}
```

**Response:** `201 Created`
```json
{
  "id": "task-uuid",
  "experiment_name": "pipeline_creation_benchmark",
  "status": "pending",
  "created_at": "2026-01-26T10:00:00",
  "started_at": null,
  "completed_at": null,
  "error": null,
  "metadata": {}
}
```

**Parameters:**
- `run_async` (boolean): If `true`, task is queued for background execution. If `false`, task executes synchronously (may timeout for long-running experiments).

### List Tasks

**GET** `/tasks?status=pending&limit=100`

List tasks, optionally filtered by status.

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `running`, `completed`, `failed`, `cancelled`)
- `limit` (optional): Maximum number of tasks to return (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "task-uuid-1",
    "experiment_name": "experiment-1",
    "status": "completed",
    ...
  },
  {
    "id": "task-uuid-2",
    "experiment_name": "experiment-2",
    "status": "running",
    ...
  }
]
```

### Get Task

**GET** `/tasks/{task_id}`

Get task details by ID.

**Response:** `200 OK`
```json
{
  "id": "task-uuid",
  "experiment_name": "pipeline_creation_benchmark",
  "status": "completed",
  "created_at": "2026-01-26T10:00:00",
  "started_at": "2026-01-26T10:00:01",
  "completed_at": "2026-01-26T10:05:30",
  "error": null,
  "metadata": {}
}
```

### Get Task Result

**GET** `/tasks/{task_id}/result`

Get task execution result (only available for completed tasks).

**Response:** `200 OK`
```json
{
  "task_id": "task-uuid",
  "experiment_run": {
    "experiment_id": "exp-uuid",
    "run_id": "run-uuid",
    "dataset_id": "dataset-uuid",
    "scores": [
      {
        "name": "deep_diff_v3",
        "value": 0.85,
        "eval_id": "deep_diff_v3.v1",
        "comment": "",
        "metadata": {}
      }
    ],
    "metadata": {},
    "created_at": "2026-01-26T10:05:30"
  },
  "execution_time_seconds": 329.5,
  "metadata": {
    "model": "claude-3-7-sonnet-20250219",
    "dataset_size": 18,
    "scorers": ["deep_diff_v3"]
  }
}
```

### Get Task Run

**GET** `/tasks/{task_id}/run`

Get experiment run details from task result.

**Response:** `200 OK`
```json
{
  "experiment_id": "exp-uuid",
  "run_id": "run-uuid",
  "dataset_id": "dataset-uuid",
  "scores": [...],
  "metadata": {...},
  "created_at": "2026-01-26T10:05:30"
}
```

### Cancel Task

**DELETE** `/tasks/{task_id}`

Cancel a pending or running task.

**Response:** `204 No Content`

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service not ready

## Example Usage

### Python

```python
import requests

# Create experiment
response = requests.post(
    "http://localhost:8000/experiments",
    json={
        "experiment_name": "my_experiment",
        "config": {...},
        "run_async": True,
    }
)
task = response.json()

# Check status
task_id = task["id"]
status_response = requests.get(f"http://localhost:8000/tasks/{task_id}")
print(status_response.json())

# Get result when completed
result_response = requests.get(f"http://localhost:8000/tasks/{task_id}/result")
print(result_response.json())
```

### cURL

```bash
# Create experiment
curl -X POST http://localhost:8000/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "my_experiment",
    "config": {...},
    "run_async": true
  }'

# Get task status
curl http://localhost:8000/tasks/{task_id}

# Get result
curl http://localhost:8000/tasks/{task_id}/result
```

## OpenAPI Schema

The API includes automatic OpenAPI/Swagger documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Background Worker

The API includes a background worker that automatically processes pending tasks. The worker:

- Polls for pending tasks every second
- Executes up to 3 tasks concurrently (configurable)
- Handles errors gracefully
- Logs execution progress

## Task Lifecycle

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
```

Tasks can be cancelled when in `PENDING` or `RUNNING` status.

## Agent-Based Endpoints

The platform uses an agent-based architecture where each evaluation capability is handled by a dedicated agent. This provides modularity, testability, and extensibility.

### Dataset Agent Endpoints

#### Load Dataset

**POST** `/evaluate/dataset/load`

Load a dataset from various sources (JSONL, Index CSV, or function-based).

**Request Body:**
```json
{
  "dataset_type": "index_csv",
  "path": "benchmarks/datasets/index.csv",
  "index_file": "benchmarks/datasets/index.csv",
  "base_dir": "benchmarks/datasets",
  "filters": {
    "entity_type": "pipeline",
    "operation_type": "create"
  },
  "offline": false,
  "actual_suffix": "actual"
}
```

**Response:** `200 OK`
```json
{
  "item_count": 18,
  "items": [...]
}
```

#### Validate Dataset

**POST** `/evaluate/dataset/validate`

Validate dataset format and structure.

**Request Body:**
```json
{
  "dataset_type": "jsonl",
  "path": "data/dataset.jsonl"
}
```

**Response:** `200 OK`
```json
{
  "valid": true,
  "item_count": 18,
  "issues": []
}
```

#### List Datasets

**GET** `/evaluate/dataset/list?base_dir=benchmarks/datasets`

List available datasets in a directory.

**Response:** `200 OK`
```json
{
  "datasets": [
    {
      "type": "jsonl",
      "path": "/path/to/dataset.jsonl",
      "name": "dataset.jsonl"
    }
  ]
}
```

### Scorer Agent Endpoints

#### Create Scorer

**POST** `/evaluate/scorer/create`

Create a scorer instance.

**Request Body:**
```json
{
  "scorer_type": "deep_diff",
  "name": "my_scorer",
  "config": {
    "version": "v3",
    "entity_type": "pipeline"
  }
}
```

**Response:** `201 Created`
```json
{
  "scorer_id": "my_scorer",
  "name": "deep_diff_v3",
  "type": "DeepDiffScorer"
}
```

#### Score Item

**POST** `/evaluate/scorer/score`

Score a single dataset item.

**Request Body:**
```json
{
  "scorer_id": "my_scorer",
  "item": {
    "id": "test-001",
    "input": {...},
    "expected": {...}
  },
  "output": "generated yaml content"
}
```

**Response:** `200 OK`
```json
{
  "score": {
    "name": "deep_diff_v3",
    "value": 0.85,
    "eval_id": "deep_diff_v3.v1",
    "comment": null,
    "metadata": {}
  }
}
```

#### List Scorers

**GET** `/evaluate/scorer/list`

List available scorers and scorer types.

**Response:** `200 OK`
```json
{
  "cached": [
    {
      "id": "my_scorer",
      "name": "deep_diff_v3",
      "type": "DeepDiffScorer"
    }
  ],
  "available_types": [...]
}
```

### Adapter Agent Endpoints

#### Create Adapter

**POST** `/evaluate/adapter/create`

Create an adapter for AI system integration.

**Request Body:**
```json
{
  "adapter_type": "ml_infra",
  "name": "my_adapter",
  "config": {
    "base_url": "http://localhost:8000",
    "auth_token": "your-token",
    "account_id": "account-123",
    "org_id": "org-456",
    "project_id": "project-789"
  }
}
```

**Response:** `201 Created`
```json
{
  "adapter_id": "my_adapter",
  "type": "HTTPAdapter"
}
```

#### Generate Output

**POST** `/evaluate/adapter/generate`

Generate output using an adapter.

**Request Body:**
```json
{
  "adapter_id": "my_adapter",
  "input_data": {
    "prompt": "Create a pipeline...",
    "entity_type": "pipeline",
    "operation_type": "create"
  },
  "model": "claude-3-5-sonnet-20241022",
  "config": {}
}
```

**Response:** `200 OK`
```json
{
  "output": "generated yaml content"
}
```

#### List Adapters

**GET** `/evaluate/adapter/list`

List available adapters and adapter types.

**Response:** `200 OK`
```json
{
  "cached": [
    {
      "id": "my_adapter",
      "type": "HTTPAdapter"
    }
  ],
  "available_types": [...]
}
```

### Experiment Agent Endpoints

#### Create Experiment

**POST** `/evaluate/experiment/create`

Create an experiment configuration.

**Request Body:**
```json
{
  "name": "pipeline_creation_benchmark",
  "dataset_config": {
    "type": "index_csv",
    "index_file": "benchmarks/datasets/index.csv",
    "base_dir": "benchmarks/datasets",
    "filters": {
      "entity_type": "pipeline",
      "operation_type": "create"
    }
  },
  "scorers_config": [
    {
      "type": "deep_diff",
      "version": "v3"
    }
  ],
  "experiment_id": null
}
```

**Response:** `201 Created`
```json
{
  "experiment_id": "exp-uuid",
  "name": "pipeline_creation_benchmark",
  "dataset_size": 18,
  "scorer_count": 1
}
```

#### Run Experiment

**POST** `/evaluate/experiment/run`

Run an experiment.

**Request Body:**
```json
{
  "experiment_id": "exp-uuid",
  "adapter_config": {
    "type": "ml_infra",
    "base_url": "http://localhost:8000"
  },
  "model": "claude-3-5-sonnet-20241022",
  "concurrency_limit": 5
}
```

**Response:** `200 OK`
```json
{
  "run_id": "run-uuid",
  "experiment_id": "exp-uuid",
  "scores": [...],
  "metadata": {...}
}
```

#### Compare Runs

**POST** `/evaluate/experiment/compare`

Compare two experiment runs.

**Request Body:**
```json
{
  "run1_id": "run-uuid-1",
  "run2_id": "run-uuid-2"
}
```

**Response:** `200 OK`
```json
{
  "comparison": {
    "run1_id": "run-uuid-1",
    "run2_id": "run-uuid-2",
    "comparison": "Not implemented yet"
  }
}
```

### Task Agent Endpoints (Enhanced)

#### Create Task

**POST** `/evaluate/task/create`

Create an evaluation task using the task agent.

**Request Body:**
```json
{
  "experiment_name": "my_experiment",
  "config": {
    "dataset": {...},
    "scorers": [...],
    "adapter": {...},
    "execution": {
      "concurrency_limit": 5
    }
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "task-uuid",
  "experiment_name": "my_experiment",
  "status": "pending",
  ...
}
```

#### Get Task Status

**GET** `/evaluate/task/{task_id}`

Get task status using the task agent.

**Response:** `200 OK`
```json
{
  "id": "task-uuid",
  "status": "running",
  ...
}
```

#### Cancel Task

**DELETE** `/evaluate/task/{task_id}`

Cancel a task using the task agent.

**Response:** `200 OK`
```json
{
  "id": "task-uuid",
  "status": "cancelled",
  ...
}
```

### Unified Evaluation Endpoint

#### Unified Evaluation

**POST** `/evaluate/unified`

Unified evaluation endpoint that orchestrates all agents for end-to-end evaluation (similar to `/chat/unified` in ml-infra).

**Request Body:**

Single model (backward compatible):
```json
{
  "experiment_name": "pipeline_creation_benchmark",
  "dataset_config": {
    "type": "index_csv",
    "index_file": "benchmarks/datasets/index.csv",
    "base_dir": "benchmarks/datasets",
    "filters": {
      "entity_type": "pipeline",
      "operation_type": "create"
    }
  },
  "scorers_config": [
    {
      "type": "deep_diff",
      "version": "v3"
    }
  ],
  "adapter_config": {
    "type": "ml_infra",
    "base_url": "http://localhost:8000"
  },
  "model": "claude-3-5-sonnet-20241022",
  "concurrency_limit": 5,
  "run_async": false
}
```

Multiple models (new):
```json
{
  "experiment_name": "pipeline_creation_benchmark",
  "dataset_config": {
    "type": "index_csv",
    "index_file": "benchmarks/datasets/index.csv",
    "base_dir": "benchmarks/datasets",
    "filters": {
      "entity_type": "pipeline",
      "operation_type": "create"
    }
  },
  "scorers_config": [
    {
      "type": "deep_diff",
      "version": "v3"
    },
    {
      "type": "deep_diff",
      "version": "v2"
    }
  ],
  "adapter_config": {
    "type": "ml_infra",
    "base_url": "http://localhost:8000"
  },
  "models": ["claude-3-7-sonnet-20250219", "gpt-4o"],
  "concurrency_limit": 5,
  "run_async": false
}
```

**Response:** `200 OK`

If `run_async=true`:
```json
{
  "task_id": "task-uuid",
  "run_id": null,
  "runs": null,
  "experiment_id": "pipeline_creation_benchmark",
  "scores": null,
  "comparison": null,
  "metadata": {}
}
```

If `run_async=false` and single model:
```json
{
  "task_id": null,
  "run_id": "run-uuid",
  "runs": null,
  "experiment_id": "exp-uuid",
  "scores": [...],
  "comparison": null,
  "metadata": {...}
}
```

If `run_async=false` and multiple models:
```json
{
  "task_id": null,
  "run_id": null,
  "runs": [
    {
      "experiment_id": "exp-uuid",
      "run_id": "run-uuid-1",
      "dataset_id": "dataset-id",
      "scores": [...],
      "metadata": {...},
      "created_at": "2026-01-27T10:00:00"
    },
    {
      "experiment_id": "exp-uuid",
      "run_id": "run-uuid-2",
      "dataset_id": "dataset-id",
      "scores": [...],
      "metadata": {...},
      "created_at": "2026-01-27T10:05:00"
    }
  ],
  "experiment_id": "exp-uuid",
  "scores": null,
  "comparison": {
    "scoreboard": {
      "deep_diff_v3": {
        "claude-3-7-sonnet-20250219": {
          "mean": 0.95,
          "count": 10,
          "total": 10
        },
        "gpt-4o": {
          "mean": 0.92,
          "count": 10,
          "total": 10
        }
      }
    },
    "summary": {
      "total_models": 2,
      "total_scorers": 1,
      "scorers": ["deep_diff_v3"],
      "models": ["claude-3-7-sonnet-20250219", "gpt-4o"]
    },
    "model_scores": {...}
  },
  "metadata": {"model_count": 2}
}
```

## Agent Architecture

The platform uses an agent-based architecture where:

- **DatasetAgent**: Handles dataset loading and management
- **ScorerAgent**: Manages scoring logic and scorer creation
- **AdapterAgent**: Handles AI system integration (ML Infra, Langfuse, etc.)
- **ExperimentAgent**: Orchestrates experiment execution
- **TaskAgent**: Manages task lifecycle and execution
- **EvaluationAgent**: High-level unified orchestrator

Each agent:
- Has a dedicated set of REST endpoints
- Can be tested independently
- Includes observability hooks (Langfuse tracing, logging)
- Follows a consistent interface pattern

## Observability

All agents include:
- **Logging**: Structured logging with operation names and timing
- **Langfuse Tracing**: Optional Langfuse integration for distributed tracing (if Langfuse is installed)
- **Performance Metrics**: Execution time tracking per operation

## Migration from Legacy Endpoints

The legacy endpoints (`/experiments`, `/tasks`) are still available for backward compatibility. New code should use the agent-based endpoints (`/evaluate/*`) for better modularity and extensibility.
