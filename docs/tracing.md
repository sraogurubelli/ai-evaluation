# Tracing and cost extraction

ai-evaluation supports **Bring Your Own Tracing** (BYOT): read traces from your existing tracing system (Langfuse, OpenTelemetry/Jaeger) and optionally extract cost and token data for scores and runs.

## Concepts

- **TracingAdapter** — Interface for *reading* traces (get_trace, get_cost_data, list_traces). Implementations: Langfuse, OpenTelemetry (Jaeger HTTP API).
- **Adapter** (in `aieval.adapters`) — Interface for *generating* outputs (e.g. HTTPAdapter). Separate from TracingAdapter.
- **Cost placement** — Optional cost/token data can live in:
  - **Score.metadata** — Per-datapoint: `cost`, `input_tokens`, `output_tokens`, `provider`, `model` when a score is linked to a trace (`trace_id`).
  - **EvalResult.metadata** — Result-level: `aggregate_metrics: { accuracy, cost, latency_sec, input_tokens, output_tokens }`.

## Optional extras

- **aieval[tracing-langfuse]** — LangfuseTracingAdapter (read traces and cost from Langfuse). Langfuse may already be installed for LangfuseSink.
- **aieval[tracing-otel]** — OpenTelemetryAdapter (read from Jaeger HTTP API). Adds `httpx`.

Core install (`pip install aieval`) does not require tracing backends; use extras when you need them.

## Configuration

Example (YAML or env):

```yaml
tracing:
  adapter: langfuse   # or opentelemetry, none
  langfuse:
    host: https://cloud.langfuse.com
    # secret_key, public_key from env (LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY)
  opentelemetry:
    endpoint: http://jaeger:16686
```

Secrets: use environment variables (e.g. `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`). See `.env.example`.

## Usage

1. **Create a TracingAdapter** — Use `aieval.tracing.create_tracing_adapter(adapter_type="langfuse", **config)` or instantiate `LangfuseTracingAdapter` / `OpenTelemetryTracingAdapter` directly.
2. **Get cost for a trace** — When a score has `trace_id`, call `adapter.get_cost_data(trace_id)` and attach the result to `Score.metadata` or aggregate into run metadata.
3. **Result-level aggregates** — Call `aieval.tracing.aggregates.enrich_run_aggregate_metrics(run, tracing_adapter)` to compute `aggregate_metrics` from scores and tracing and set `EvalResult.metadata["aggregate_metrics"]`.
4. **Adapter → Score flow** — Adapters may return `GenerateResult(output, trace_id=..., observation_id=...)` instead of raw output. Use `result.output` as the model output and attach `result.trace_id` / `result.observation_id` to the Score so scores can be sent to Langfuse and cost can be read back via TracingAdapter.

## Attribute conventions

Cost extraction uses OpenTelemetry-style attribute names where available: `llm.token_count.input`, `llm.token_count.output`, `llm.cost`, `llm.provider`, `llm.model`. See `aieval.tracing.conventions` and `extract_cost_from_span_attributes()`.

## Architecture

Tracing sits alongside the evaluation flow: adapters generate outputs; scorers produce scores (with optional `trace_id`); TracingAdapters read from your backend to enrich scores or runs with cost. Cost persistence and canary analysis stay in the consuming platform (e.g. SynteraIQ).
