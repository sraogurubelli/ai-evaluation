# Production Checklist

- **Secrets:** In secrets manager; no keys in config. TLS, CORS, rate limiting, auth.
- **Infra:** Resource limits, health checks, autoscaling, DB pooling, backups.
- **Observability:** Prometheus/Grafana, tracing, log aggregation, alerting.
- **Config:** Env documented; migrations tested; log level INFO/WARNING.

See [docker](docker.md), [kubernetes](kubernetes.md), [monitoring](monitoring.md), [troubleshooting](troubleshooting.md).
