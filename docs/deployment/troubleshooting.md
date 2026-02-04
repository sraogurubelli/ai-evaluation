# Troubleshooting

- **App won't start:** Check logs (`docker logs ...` or `kubectl logs ...`). Verify env vars and `DATABASE_URL`. `curl .../health/ready`.
- **DB connection:** Ensure PostgreSQL is running. Test: `psql -U aieval -d aieval -c "SELECT 1"`. Check `DATABASE_URL` format and network.
- **Port in use:** Change port in compose or deployment.
- **Import errors:** `pip install -e .` in correct venv.

See [docker](docker.md), [operations/runbook](../operations/runbook.md).
