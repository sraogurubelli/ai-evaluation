# Getting Started

## Installation

```bash
# Clone repository
git clone <repo-url>
cd ai-evolution

# Install
pip install -e .

# Install optional dependencies for LLM judge
pip install -e ".[llm]"
```

## Configuration

1. Copy `.env.example` to `.env`
2. Set environment variables:
   - `CHAT_BASE_URL`: ml-infra server URL
   - `CHAT_PLATFORM_AUTH_TOKEN`: Authentication token
   - `LANGFUSE_*`: Optional Langfuse configuration

## Quick Start

### 1. Create Config File

Create `config.yaml`:

```yaml
experiment:
  name: "my_experiment"

dataset:
  type: "index_csv"
  index_file: "benchmarks/datasets/index.csv"
  base_dir: "benchmarks/datasets"
  filters:
    entity_type: "pipeline"
    operation_type: "create"

adapter:
  type: "ml_infra"
  base_url: "${CHAT_BASE_URL}"
  auth_token: "${CHAT_PLATFORM_AUTH_TOKEN}"

models:
  - "claude-3-7-sonnet-20250219"

scorers:
  - type: "deep_diff"
    version: "v3"

execution:
  concurrency_limit: 5

output:
  sinks:
    - type: "csv"
      path: "results/results.csv"
    - type: "stdout"
```

### 2. Run Experiment

```bash
ai-evolution run --config config.yaml
```

### 3. View Results

Results are written to:
- CSV file: `results/results.csv`
- Console: Summary printed to stdout
- Langfuse: If configured, scores linked to traces

## Examples

See `examples/` directory for:
- `ml_infra/config.yaml`: Pipeline evaluation example
- `ml_infra/config_dashboard.yaml`: Dashboard evaluation example
- `general/simple_eval.py`: Simple Python example

## Next Steps

- Read [Architecture](architecture.md) for system design
- Read [Migration Guide](migration-guide.md) to migrate from ml-infra/evals
- Explore example configs in `examples/`
