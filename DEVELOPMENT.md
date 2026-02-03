# Development

## New developer / handover

- **Run tests:** `task test` or `PYTHONPATH=. pytest tests/ -v`. SDK/consumer: `tests/unit/test_sdk_devops.py`, `tests/unit/test_sdk_unit_test.py`.
- **Docs:** [README](README.md), [getting-started](docs/getting-started.md), [sdk-unit-testing](docs/sdk-unit-testing.md).
- **Consumer sample:** `samples_sdk/consumers/devops` — run from repo root with `PYTHONPATH=.`.
- **Known limitations:** [Below](#known-limitations--not-yet-implemented).
- **Env:** Copy `.env.example` to `.env` and fill required vars.

## Prerequisites

- Python 3.11+
- [Task](https://taskfile.dev/) (optional but recommended)
- Docker (optional; for PostgreSQL)

## Setup

**Fresh start (recommended first time):** `task fresh` — cleans artifacts, venv, DB volumes; creates venv, installs deps, starts DB, runs migrations.

**Standard:** `task setup` — venv, editable install, dev deps, copy `.env`, start DB. Then `task db-migrate`.

**Without Task:** `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -e ".[dev]"`.

## Tasks

| Area | Commands |
|------|----------|
| Setup | `task fresh`, `task setup`, `task venv`, `task install`, `task install-dev`, `task copy-env` |
| Code quality | `task lint`, `task lint-fix`, `task format`, `task typecheck`, `task check` |
| Tests | `task test`, `task test-unit`, `task test-integration`, `task test-coverage` |
| Server | `task server`, `task server-prod` |
| DB | `task db-up`, `task db-down`, `task db-migrate`, `task db-reset`, `task db-shell` |
| Cleanup | `task clean`, `task clean-venv`, `task clean-build` |
| Workflow | `task dev` (format, lint, test), `task pre-commit` (format, lint, typecheck, test) |

Run `task --list` for full list.

## Run tests

```bash
task test
# or
PYTHONPATH=. pytest tests/ -v
```

Unit tests: `tests/unit/`. Integration: `tests/integration/`. Fixtures: `tests/fixtures/`, `tests/conftest_devops.py`.

## Env

Copy `.env.example` to `.env`. Essential: `CHAT_BASE_URL`, `CHAT_PLATFORM_AUTH_TOKEN`, `DATABASE_URL`. For DB via Docker: `task db-up` then use `POSTGRES_*` / `DATABASE_URL` from `.env.example`. Full list in `.env.example`.

## Code style

Ruff (format + lint), MyPy. Line length 100. Run `task format` before commit.

## Known limitations / Not yet implemented

- **CLI** (`src/aieval/cli/main.py`): Dataset type `function` and `compare --run1/--run2` not implemented.
- **Langfuse adapter** (`src/aieval/adapters/langfuse.py`): Trace reading not implemented (placeholder).

## Contributing

1. Create a feature branch.
2. Make changes; run `task pre-commit`.
3. Add/update tests.
4. Open a pull request.

## Resources

[Task](https://taskfile.dev/) · [FastAPI](https://fastapi.tiangolo.com/) · [Ruff](https://docs.astral.sh/ruff/) · [MyPy](https://mypy.readthedocs.io/)
