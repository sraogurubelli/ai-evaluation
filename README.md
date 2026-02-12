# AI Evaluation

Unified AI **agent evaluation** platform. Open source, self-hostable.

**Agent evaluation only.** Not ML experiments. Not feature-flag experiments.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What it does

- **Evals**: Multiple data set formats (JSONL, index CSV), scorers (DeepDiff, LLM-as-judge), runs and scores
- **Adapters**: HTTP/SSE; sample DevOps consumer in `samples_sdk/consumers/devops`
- **API & UI**: FastAPI server, Gradio UI; PostgreSQL for persistence

See [Concepts](docs/concepts.md) for Eval, Run, Data Set, Task, Trace, and Scores.

## Install

Requires **Python 3.11+**. Pip will refuse to install on older Python (see `requires-python` in `pyproject.toml`).

Choose one of the following.

### Option 1: pip install (create a virtual environment first)

Create a venv so this project’s dependencies don’t affect other work, then install:

```bash
# 1. Create a virtual environment with Python 3.11+
python3.11 -m venv .venv

# 2. Activate the venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 3. Upgrade pip and install the package
pip install --upgrade pip
pip install -e .

# Optional: LLM judge support
# pip install -e ".[llm]"
```

**With [uv](https://github.com/astral-sh/uv)** (creates venv and installs in one go):

```bash
uv venv && source .venv/bin/activate && uv pip install -e .
```

### Option 2: task fresh (full dev environment + DB)

If you use [Task](https://taskfile.dev/) and Docker, this cleans everything, creates a venv, installs the package and dev deps, starts PostgreSQL, and runs migrations:

```bash
task fresh
```

Then start the server with `task server` and run tests with `task test`. See [DEVELOPMENT.md](DEVELOPMENT.md) for all tasks (`task --list`).

## Run

**SDK**

Define an **Eval** (name, data set, scorers) and run it to get a **Run** with **Scores**. In the SDK, an Eval is represented by the `Experiment` class.

```python
from aieval import Experiment, HTTPAdapter, DeepDiffScorer, load_jsonl_dataset

dataset = load_jsonl_dataset("dataset.jsonl")
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="your-token")
experiment = Experiment(name="my_eval", dataset=dataset, scorers=[DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")])
result = await experiment.run(adapter=adapter, model="gpt-4o")
```

**CLI**

Run an eval from a config file:

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

## License and maintainer

This is an **independent open source project**. MIT. See [LICENSE](LICENSE).  
**Copyright (c) 2026 Srinivasa Rao Gurubelli (VP of Engineering & Fellow).**  
Contributions welcome from anyone; see [CONTRIBUTING.md](CONTRIBUTING.md) and [DEVELOPMENT.md](DEVELOPMENT.md).
