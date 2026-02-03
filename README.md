# AI Evaluation

Unified AI evaluation and experimentation platform. Open source, self-hostable.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What it does

- **Evaluation**: Multiple dataset formats (JSONL, index CSV), scorers (DeepDiff, LLM-as-judge), experiment tracking
- **Adapters**: HTTP/SSE; sample DevOps consumer in `samples_sdk/consumers/devops`
- **API & UI**: FastAPI server, Gradio UI; PostgreSQL for persistence

## Install

```bash
pip install -e .
# Optional: pip install -e ".[llm]"   # LLM judge
# Dev: task fresh   # full env + DB (see DEVELOPMENT.md)
```

## Run

**SDK**

```python
from aieval import Experiment, HTTPAdapter, DeepDiffScorer, load_jsonl_dataset

dataset = load_jsonl_dataset("dataset.jsonl")
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="your-token")
experiment = Experiment(name="my_eval", dataset=dataset, scorers=[DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")])
result = await experiment.run(adapter=adapter, model="gpt-4o")
```

**CLI**

```bash
aieval run --config examples/ml_infra/config.yaml
```

**API server**

```bash
aieval-server
# API: http://localhost:7890  |  Swagger: /docs  |  ReDoc: /redoc
```

**Unit testing** (framework helpers in `aieval.sdk.unit_test`): See [docs/sdk-unit-testing.md](docs/sdk-unit-testing.md). For index-CSV + CSV sinks, use `samples_sdk/consumers/devops` (run with `PYTHONPATH=.` from repo root).

## Documentation

- [Getting Started](docs/getting-started.md)
- [SDK](docs/sdk.md) · [API](docs/api.md) · [Architecture](docs/architecture.md)
- [Migration](docs/migration.md) · [Deployment](docs/deployment/docker.md)

## Config

Copy `.env.example` to `.env`. Essential: `CHAT_BASE_URL`, `CHAT_PLATFORM_AUTH_TOKEN`, `DATABASE_URL` (or `task db-up`). See file for full list.

## Known limitations

- CLI: dataset type `function` and `compare --run1/--run2` not implemented
- Langfuse adapter: trace reading not implemented (placeholder)

Details in [DEVELOPMENT.md](DEVELOPMENT.md).

## Project structure

```
ai-evaluation/
├── src/aieval/     # Core, adapters, scorers, datasets, sinks, api, cli
├── tests/
├── examples/
└── docs/
```

## License

MIT. See [LICENSE](LICENSE). Contributions welcome (see [DEVELOPMENT.md](DEVELOPMENT.md)).
