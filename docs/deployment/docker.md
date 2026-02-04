# Docker Deployment

## Quick start

1. `cp .env.example .env` and edit.
2. `docker compose -f docker-compose.prod.yml up -d`
3. API: http://localhost:7890, docs: /docs, health: /health

**Direct run:** `docker build -t aieval:latest .` then `docker run -d -p 7890:7890 -e DATABASE_URL=... aieval:latest`

## Config

Key env: `DATABASE_URL`, `POSTGRES_PASSWORD`, `LOG_LEVEL`. Full list in `.env.example`.

## Health

- `/health` — basic
- `/health/live`, `/health/ready`, `/health/startup` — for Kubernetes

## Monitoring (optional)

`docker compose -f docker-compose.prod.yml --profile monitoring up -d`. Prometheus: 9090, Grafana: 3000.

## Troubleshooting

- Logs: `docker logs ai-evolution-app` (or app container name)
- DB: ensure PostgreSQL is running; check `DATABASE_URL`
- Port: change in compose if 7890 is in use

See [kubernetes](kubernetes.md), [production](production.md), [monitoring](monitoring.md), [troubleshooting](troubleshooting.md).
