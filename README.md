# AI Evaluation

Unified AI evaluation and experimentation platform. Open source, self-hostable.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What it does

- **Evaluation**: Multiple dataset formats (JSONL, index CSV), scorers (exact match, contains, regex, DeepDiff, LLM-as-judge), experiment tracking
- **Adapters**: HTTP/SSE; sample DevOps consumer in `samples_sdk/consumers/devops`
- **API & UI**: FastAPI server, Gradio UI; PostgreSQL for persistence

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

```python
from aieval import Experiment, HTTPAdapter, ExactMatchScorer, ContainsScorer, load_jsonl_dataset

dataset = load_jsonl_dataset("dataset.jsonl")
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="your-token")
scorers = [
    ExactMatchScorer(name="exact", eval_id="exact.v1"),
    ContainsScorer(name="keywords", eval_id="keywords.v1", require_all=True)
]
experiment = Experiment(name="my_eval", dataset=dataset, scorers=scorers)
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
- [Metrics and Scorers](docs/metrics-and-scorers.md)
- [Migration](docs/migration.md) · [Deployment](docs/deployment/docker.md)

## Available Scorers

### Deterministic Scorers (Fast, No External Calls)
- **ExactMatchScorer** - Exact string equality check
- **ContainsScorer** - Substring presence check (single or multiple)
- **RegexMatchScorer** - Regex pattern matching (single or multiple)

### Structural Comparison
- **DeepDiffScorer** (v1, v2, v3) - YAML/JSON structural comparison with versioned strictness

### Semantic Evaluation
- **LLMJudgeScorer** - LLM-based rubric evaluation (requires `.[llm]` install)
- **SchemaValidationScorer** - Schema validation against expected structure

### Domain-Specific
- **DashboardQualityScorer** - Dashboard entity quality metrics
- **KnowledgeGraphQualityScorer** - Knowledge graph quality metrics

### Performance Metrics
- **LatencyScorer** - Execution time measurement
- **TokenUsageScorer** - Token consumption tracking
- **ToolCallScorer** - Tool invocation metrics

See [docs/metrics-and-scorers.md](docs/metrics-and-scorers.md) for detailed usage and configuration.

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
