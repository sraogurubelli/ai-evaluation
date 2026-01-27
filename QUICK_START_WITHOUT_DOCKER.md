# Running AI Evolution Without Docker

If you don't have Docker installed, you can still use most features of AI Evolution.

## What Requires Docker

- **PostgreSQL Database** - Used for task storage and experiment tracking
- **Temporal Server** - Used for workflow orchestration (optional)

## What Works Without Docker

- **CLI Execution** - Run experiments directly via CLI
- **SDK Usage** - Use the Python SDK programmatically
- **In-Memory Mode** - Use in-memory storage (no persistence)

## Options

### Option 1: Install Docker (Recommended)

```bash
# macOS
brew install --cask docker

# Then start Docker Desktop and run:
task fresh
```

### Option 2: Use External PostgreSQL

If you have PostgreSQL installed locally:

```bash
# Update .env with your PostgreSQL connection
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_evolution

# Skip database tasks
task venv
task install-dev
task db-migrate  # Uses your external PostgreSQL
```

### Option 3: Use Temporal Cloud

If you want Temporal workflows but don't want to run Temporal locally:

```bash
# Set Temporal Cloud credentials in .env
TEMPORAL_HOST=your-namespace.temporal.io:7233
TEMPORAL_NAMESPACE=your-namespace
TEMPORAL_TLS_CERT_PATH=/path/to/cert.pem
TEMPORAL_TLS_KEY_PATH=/path/to/key.pem

# Skip temporal-up task
task temporal-worker  # Connects to Temporal Cloud
```

### Option 4: Skip Database/Temporal Tasks

For basic CLI usage, you can skip database setup:

```bash
# Just use CLI without database
task venv
task install-dev
ai-evolution run --config examples/ml_infra/config.yaml
```

## Minimal Setup (No Docker)

```bash
# 1. Create venv
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

# 3. Use CLI (no database needed for basic usage)
ai-evolution run --config examples/ml_infra/config.yaml
```

## What You'll Miss Without Docker

- **Task persistence** - Tasks won't be stored in database
- **Experiment tracking** - No long-term experiment history
- **Temporal workflows** - No durable workflow execution
- **API server** - FastAPI server requires database

## Recommendation

For development, Docker is recommended because:
- Easy PostgreSQL setup
- Easy Temporal setup
- Consistent environment
- All features available

But for quick testing or CI/CD, you can use the CLI without Docker.
