# Operations Runbook

**Health:** `curl http://localhost:7890/health/ready`

**Logs:** `docker logs ai-evolution-app --tail 100` (or app container name). Errors: `grep -i error`.

**Metrics:** Prometheus (9090), Grafana (3000). Request rate, errors, latency, DB usage.

**DB:** Check PostgreSQL is up; run migrations if needed: `alembic upgrade head`.

See [deployment](../deployment/) and [incident-response](incident-response.md).
