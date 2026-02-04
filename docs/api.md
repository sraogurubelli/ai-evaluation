# API

REST API for experiments and tasks. Base URL: `http://localhost:7890` (or port in config). No auth by default; add middleware for production.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health and task counts |
| POST | `/experiments` | Create/run experiment (body: `experiment_name`, `config`, `run_async`) |
| GET | `/tasks` | List tasks (query: `status`, `limit`) |
| GET | `/tasks/{task_id}` | Task details |
| GET | `/tasks/{task_id}/result` | Task result (scores, run) |
| GET | `/tasks/{task_id}/run` | Experiment run from task |

## Usage

**Create and run experiment (async):**

```bash
curl -X POST http://localhost:7890/experiments \
  -H "Content-Type: application/json" \
  -d '{"experiment_name": "my_eval", "config": {...}, "run_async": true}'
```

**Poll result:**

```bash
curl http://localhost:7890/tasks/{task_id}/result
```

**Interactive docs:** `/docs` (Swagger), `/redoc` (ReDoc).
