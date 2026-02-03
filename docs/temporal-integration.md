# Temporal Integration

Optional: long-running workflows with durable execution, retries, and audit trail.

**Run worker:** Start Temporal server (or use Temporal Cloud), then run the aieval worker so it executes experiment workflows and activities. See `src/aieval/workflows/` (workflows, activities, worker). Config: `TEMPORAL_*` in `.env.example`.

**When to use:** If you need durable experiment runs across restarts or distributed workers. For most CLI/SDK evals, Temporal is not required.
