# Monitoring

- **Prometheus:** Scrape `/metrics`. HTTP, experiment, task, DB, adapter, scorer metrics.
- **Health:** `/health`, `/health/live`, `/health/ready`, `/health/startup`
- **Tracing:** OpenTelemetry. **Logging:** JSON with correlation IDs.

Add target to `prometheus.yml`; use Grafana for dashboards. See [docker](docker.md) for monitoring profile.
