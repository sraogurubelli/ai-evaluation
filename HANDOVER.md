# Handover checklist

Quick checklist for new developers. For full setup and details, see [README](README.md) and [DEVELOPMENT.md](DEVELOPMENT.md).

- **Run tests:** `task test` or `PYTHONPATH=. pytest tests/ -v`
  - SDK/consumer: `tests/unit/test_sdk_devops.py`, `tests/unit/test_sdk_unit_test.py`
- **Docs:** [README](README.md), [getting-started.md](docs/getting-started.md), [sdk-unit-testing.md](docs/sdk-unit-testing.md), [DEVELOPMENT.md](DEVELOPMENT.md)
- **Consumer sample:** `samples_sdk/consumers/devops` — run from repo root with `PYTHONPATH=.`
- **Known limitations:** See [DEVELOPMENT.md](DEVELOPMENT.md#known-limitations--not-yet-implemented) (CLI function dataset & compare command, Langfuse adapter placeholder)
- **Env:** Copy `.env.example` to `.env` and fill required variables
