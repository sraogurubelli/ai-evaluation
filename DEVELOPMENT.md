# Development Guide

This guide covers setting up and working with the AI Evolution development environment.

## Prerequisites

- Python 3.11 or higher
- [Task](https://taskfile.dev/) - Modern task runner (install via Homebrew, Snapcraft, Scoop, or download from [taskfile.dev](https://taskfile.dev/))
- Docker and Docker Compose - For PostgreSQL database (optional but recommended)

## Quick Start

1. **Install Task** (if not already installed):
   ```bash
   # macOS
   brew install go-task/tap/go-task
   
   # Linux (using snap)
   snap install task --classic
   
   # Or download from https://taskfile.dev/installation/
   ```

2. **Set up development environment**:
   
   **Option A: Fresh start (recommended for first time)**:
   ```bash
   task fresh
   ```
   This will:
   - Clean all old artifacts and caches
   - Remove old virtual environment
   - Remove old database volumes
   - Create fresh virtual environment
   - Install all dependencies
   - Set up environment file
   - Start and initialize database
   - Run migrations
   
   **Option B: Standard setup**:
   ```bash
   task setup
   ```
   This will:
   - Create a Python virtual environment
   - Install the package in editable mode
   - Install development dependencies
   - Copy `.env.example` to `.env`
   - Start PostgreSQL database (Docker)
   
   Then run migrations:
   ```bash
   task db-migrate
   ```

   **Alternative: Using requirements.txt**:
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Start developing!**

## Available Tasks

Run `task --list` to see all available tasks, or `task` to see the default help.

### Setup & Installation

- `task fresh` - **Fresh start** - Clean everything and rebuild from scratch (recommended for first time)
- `task setup` - Set up the complete development environment
- `task venv` - Create Python virtual environment
- `task install` - Install package in editable mode
- `task install-dev` - Install development dependencies
- `task install-llm` - Install LLM dependencies (OpenAI, Anthropic)
- `task install-requirements` - Install from requirements.txt
- `task install-requirements-dev` - Install development requirements
- `task install-requirements-llm` - Install LLM requirements
- `task copy-env` - Copy `.env.example` to `.env`

### Code Quality

- `task lint` - Run Ruff linter
- `task lint-fix` - Run Ruff linter and auto-fix issues
- `task format` - Format code with Ruff
- `task typecheck` - Run MyPy type checker
- `task check` - Run all code quality checks

### Testing

- `task test` - Run all tests
- `task test-unit` - Run unit tests only
- `task test-integration` - Run integration tests only
- `task test-coverage` - Run tests with coverage report
- `task test-watch` - Run tests in watch mode (requires pytest-watch)

### Development Server

- `task server` - Start FastAPI development server (with auto-reload)
- `task server-prod` - Start FastAPI production server (with workers)

### CLI Commands

- `task cli-run` - Run CLI evaluation (uses default config)
- `task cli-compare` - Compare experiment runs via CLI

### Examples

- `task example-api` - Run API example script
- `task example-simple` - Run simple evaluation example

### Database

- `task db-up` - Start PostgreSQL database (Docker)
- `task db-down` - Stop PostgreSQL database
- `task db-restart` - Restart PostgreSQL database
- `task db-logs` - View PostgreSQL logs
- `task db-shell` - Open PostgreSQL shell (psql)
- `task db-reset` - Reset database (drop and recreate)
- `task db-migrate` - Run database migrations
- `task db-migrate-create` - Create a new migration
- `task db-migrate-downgrade` - Downgrade database by one revision
- `task db-init` - Initialize database (create tables)
- `task pgadmin` - Start pgAdmin (database management UI)
- `task pgadmin-stop` - Stop pgAdmin

### Cleanup

- `task clean` - Clean all generated files and caches
- `task clean-pyc` - Remove Python cache files
- `task clean-test` - Remove test artifacts
- `task clean-build` - Remove build artifacts
- `task clean-cache` - Remove Ruff cache
- `task clean-venv` - Remove virtual environment

### Development Workflow

- `task dev` - Run development workflow (format, lint, test)
- `task pre-commit` - Run pre-commit checks (format, lint, typecheck, test)
- `task ci` - Run CI pipeline checks

### Utilities

- `task shell` - Activate virtual environment shell
- `task version` - Show Python and package versions
- `task docs-serve` - Show documentation URLs (requires server running)

## Common Workflows

### Starting Development

```bash
# Set up environment (first time only)
task setup

# Activate shell with virtual environment
task shell

# Or manually activate
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### Making Changes

```bash
# 1. Make your code changes

# 2. Format code
task format

# 3. Check for issues
task lint

# 4. Run tests
task test

# 5. Or run everything
task dev
```

### Running the API Server

```bash
# Development mode (with auto-reload)
task server

# Production mode (with workers)
task server-prod

# Access:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Running Tests

```bash
# All tests
task test

# Unit tests only
task test-unit

# Integration tests only
task test-integration

# With coverage
task test-coverage

# Watch mode (auto-rerun on file changes)
task test-watch
```

### Before Committing

```bash
# Run pre-commit checks
task pre-commit

# This runs:
# - Format code
# - Lint code
# - Type check
# - Run tests
```

## Project Structure

```
ai-evolution/
├── src/ai_evolution/      # Main source code
│   ├── agents/            # Agent implementations
│   ├── api/               # FastAPI application
│   ├── adapters/          # AI system adapters
│   ├── core/              # Core types and experiment logic
│   ├── datasets/          # Dataset loaders
│   ├── scorers/           # Evaluation scorers
│   ├── sinks/             # Output sinks
│   └── tasks/             # Task management
├── tests/                  # Test suite
├── examples/               # Example scripts
├── docs/                   # Documentation
├── Taskfile.yml           # Task runner configuration
└── pyproject.toml         # Python project configuration
```

## Database Setup

The project uses PostgreSQL for persistent storage. The easiest way to run it locally is with Docker:

```bash
# Start database
task db-up

# Run migrations
task db-migrate

# Optional: Start pgAdmin for database management
task pgadmin
# Access at http://localhost:5050
```

The database will be available at `localhost:5432` with:
- User: `ai_evolution` (or from `POSTGRES_USER`)
- Password: `ai_evolution_dev` (or from `POSTGRES_PASSWORD`)
- Database: `ai_evolution` (or from `POSTGRES_DB`)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ML Infra Configuration
CHAT_BASE_URL=http://localhost:8000
CHAT_PLATFORM_AUTH_TOKEN=your-token
ACCOUNT_ID=default
ORG_ID=default
PROJECT_ID=default

# Langfuse (optional)
LANGFUSE_PUBLIC_KEY=your-key
LANGFUSE_SECRET_KEY=your-secret
LANGFUSE_HOST=http://localhost:3000

# LLM API Keys (for LLM judge scorer)
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# PostgreSQL Database (automatically configured for Docker)
POSTGRES_USER=ai_evolution
POSTGRES_PASSWORD=ai_evolution_dev
POSTGRES_DB=ai_evolution
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

## Code Style

- **Formatter**: Ruff (configured in `pyproject.toml`)
- **Linter**: Ruff (configured in `pyproject.toml`)
- **Type Checker**: MyPy (configured in `pyproject.toml`)
- **Line Length**: 100 characters
- **Python Version**: 3.11+

Run `task format` before committing to ensure consistent formatting.

## Testing

Tests are organized in the `tests/` directory:

- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/fixtures/` - Test fixtures and sample data

Run tests with:
```bash
task test              # All tests
task test-unit         # Unit tests only
task test-integration   # Integration tests only
task test-coverage      # With coverage report
```

## API Development

The API is built with FastAPI and includes:

- Automatic OpenAPI/Swagger documentation
- Request/response validation with Pydantic
- Agent-based architecture
- Background task execution

Start the server:
```bash
task server
```

Access documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Troubleshooting

### Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
# Remove and recreate
task clean-venv
task venv
task install
task install-dev
```

### Import Errors

Make sure the package is installed in editable mode:

```bash
task install
```

### Test Failures

Run tests with verbose output:

```bash
pytest tests/ -v -s
```

### Port Already in Use

Change the port in `Taskfile.yml`:

```yaml
vars:
  PORT: 8001  # Change from 8000
```

Or specify when running:

```bash
PORT=8001 task server
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `task pre-commit` to ensure code quality
4. Write/update tests
5. Submit a pull request

## Resources

- [Task Documentation](https://taskfile.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
