# Getting Started

## Install

```bash
git clone <repo-url>
cd ai-evaluation
pip install -e .
# Optional: pip install -e ".[llm]"
```

## Config

Copy `.env.example` to `.env`. Set `CHAT_BASE_URL`, `CHAT_PLATFORM_AUTH_TOKEN`. Optional: `LANGFUSE_*`.

## Run first experiment

**CLI:** Create `config.yaml` (see [README](../README.md) or `examples/ml_infra/config.yaml`). Then:

```bash
aieval run --config config.yaml
```

**SDK:** See [SDK](sdk.md) for `Experiment`, `HTTPAdapter`, `DeepDiffScorer`, `load_jsonl_dataset`. For index-CSV + CSV: `samples_sdk/consumers/devops` (run with `PYTHONPATH=.` from repo root).

Results: CSV path in config, stdout summary; Langfuse if configured.

## Run without Docker

- **CLI / SDK** work without Docker. For basic runs you only need a venv and `pip install -e ".[dev]"`.
- **PostgreSQL** is needed for task storage and experiment tracking. Options: install Docker and run `task db-up`; or use an existing PostgreSQL and set `DATABASE_URL` in `.env`.
- **Minimal (no DB):** `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -e ".[dev]"` → `aieval run --config config.yaml` (CLI may have limited features without DB).
- **Temporal** (workflows) is optional; skip if you only run CLI/SDK evals.

## Next steps

- [Architecture](architecture.md) · [Migration](migration.md) · [SDK unit testing](sdk-unit-testing.md)
- Examples: `examples/ml_infra/`, `examples/general/`, `samples_sdk/consumers/devops`
