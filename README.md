# AI Evolution

A unified AI evaluation and experimentation platform for testing and improving AI systems. Open source, self-hostable, and designed for production use.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Unified Evaluation System**: Support for multiple dataset formats (JSONL, index CSV, function-based)
- **Experiment Management**: Track experiments, compare runs, identify regressions
- **Flexible Scorers**: Code-based, LLM-as-judge, and entity-specific scorers
- **Flexible Adapters**: Integrate with any AI system (includes ml-infra adapter, easily extensible to OpenAI, Anthropic, etc.)
- **Optional Langfuse Integration**: Link scores to traces for full observability
- **Task Framework**: Background task execution with async support
- **REST API**: FastAPI server with automatic OpenAPI documentation
- **PostgreSQL Support**: Persistent storage for experiments, runs, and scores
- **Agent-Based Architecture**: Modular design with dedicated agents for each capability

## Quick Start

### Installation

**Recommended: Using Task (fresh start)**
```bash
# Install Task: https://taskfile.dev/installation/
# Then run:
task fresh
```
This will clean everything and set up a fresh development environment with database.

**Using pip:**
```bash
# Install core dependencies
pip install -r requirements.txt

# Install in editable mode (for development)
pip install -e .

# Install optional dependencies for LLM judge
pip install -r requirements-llm.txt
# or
pip install -e ".[llm]"
```

**Using pyproject.toml:**
```bash
# Install
pip install -e .

# Install optional dependencies for LLM judge
pip install -e ".[llm]"
```



## Web UI

AI Evolution includes a web-based UI built with Gradio for easy experiment management.

### Launch UI

```bash
# Start the API server first (in one terminal)
ai-evolution-server

# Then launch the UI (in another terminal)
python -m ai_evolution.ui.server
```

The UI will be available at `http://localhost:7860`.

### UI Features

- **Run Experiments**: Configure and run experiments through a web interface
- **View Results**: Check experiment status and view results
- **Experiment Management**: List and manage completed experiments

See [UI Documentation](docs/ui.md) for more details.

### SDK Usage (Recommended for Customers)

```python
from ai_evolution import Experiment, HTTPAdapter, DeepDiffScorer, load_jsonl_dataset

# Load dataset
dataset = load_jsonl_dataset("dataset.jsonl")

# Create adapter
adapter = HTTPAdapter(
    base_url="http://your-api.com",
    auth_token="your-token",
)

# Create experiment
experiment = Experiment(
    name="my_evaluation",
    dataset=dataset,
    scorers=[DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")],
)

# Run evaluation
result = await experiment.run(adapter=adapter, model="gpt-4o")
```

See [SDK Documentation](docs/sdk.md) for more examples.

### Unit-Level Testing (ML Infra Teams)

For unit-level evaluation testing:

```python
from ai_evolution.sdk.ml_infra import run_single_test, DeepDiffScorer, HTTPAdapter

result = await run_single_test(
    test_id="pipeline_create_001",
    index_file="benchmarks/datasets/index.csv",
    adapter=HTTPAdapter(base_url="http://localhost:8000"),
    scorer=DeepDiffScorer(version="v3"),
    model="claude-3-7-sonnet",
)

assert result.scores[0].value >= 0.9
```

See [Unit Testing Guide](docs/sdk-unit-testing.md) for comprehensive examples.

### CLI Usage

```bash
# Run an experiment
ai-evolution run --config examples/ml_infra/config.yaml  # Uses HTTPAdapter with ml-infra config
# Or use HTTPAdapter for any REST API - see examples/
```

### API Usage

```bash
# Start the API server
ai-evolution-server

# Or with uvicorn directly
uvicorn ai_evolution.api.app:create_app --host 0.0.0.0 --port 7890
```

The API will be available at:
- **API**: `http://localhost:7890`
- **Swagger UI**: `http://localhost:7890/docs`
- **ReDoc**: `http://localhost:7890/redoc`

### Example API Request

```python
import requests

# Create experiment
response = requests.post(
    "http://localhost:8000/experiments",
    json={
        "experiment_name": "my_experiment",
        "config": {
            "dataset": {...},
            "adapter": {...},
            "scorers": [...],
        },
        "run_async": True,
    }
)

task = response.json()
task_id = task["id"]

# Check status
status = requests.get(f"http://localhost:8000/tasks/{task_id}").json()

# Get result when completed
result = requests.get(f"http://localhost:8000/tasks/{task_id}/result").json()
```

## Documentation

- [Architecture](docs/architecture.md) - System design and component relationships
- [Getting Started](docs/getting-started.md) - Quick start guide
- [Migration Guide](docs/migration-guide.md) - Migrating from ml-infra/evals
- [API Documentation](docs/api.md) - REST API reference

## Project Structure

```
ai-evolution/
├── src/ai_evolution/
│   ├── core/          # Core types and experiment system
│   ├── adapters/      # AI system adapters
│   ├── scorers/       # Evaluation scorers
│   ├── datasets/      # Dataset loaders
│   ├── sinks/         # Output handlers
│   ├── tasks/         # Task framework
│   ├── api/           # FastAPI server
│   └── cli/           # CLI interface
├── tests/             # Unit and integration tests
├── examples/          # Example configs and usage
├── migrations/        # Migration tools
└── docs/              # Documentation
```

## Configuration

1. Copy `.env.example` to `.env`
2. Set environment variables:
   - `CHAT_BASE_URL`: AI system server URL (e.g., ml-infra server or your custom AI API)
   - `CHAT_PLATFORM_AUTH_TOKEN`: Authentication token (if required)
   - `DATABASE_URL`: PostgreSQL connection string (or use Docker with `task db-up`)
   - `LANGFUSE_*`: Optional Langfuse configuration for observability

**Note**: The platform includes a generic `HTTPAdapter` that can be configured for any REST API. Teams should create their own custom adapters for their specific APIs. See `docs/custom-adapters.md` for guidance.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Inspired by evaluation frameworks from Anthropic, Braintrust, Langfuse, and Promptfoo
- Built with FastAPI, SQLAlchemy, and modern Python async patterns
