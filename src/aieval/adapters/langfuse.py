"""Langfuse adapter: read model output from Langfuse traces for evaluation."""

from __future__ import annotations

import os
from typing import Any

from aieval.adapters.base import Adapter
from aieval.core.types import GenerateResult


def _get_langfuse_client(
    secret_key: str | None = None,
    public_key: str | None = None,
    host: str | None = None,
):
    """Return Langfuse client; uses env vars if args not provided."""
    from langfuse import Langfuse

    return Langfuse(
        secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY", ""),
        public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )


def _obs_to_dict(obs: Any) -> dict:
    """Convert observation to dict for safe access."""
    if obs is None:
        return {}
    if isinstance(obs, dict):
        return obs
    if hasattr(obs, "model_dump"):
        return obs.model_dump()
    if hasattr(obs, "dict"):
        return obs.dict()
    return {}


def _extract_output_from_observation(obs: Any) -> str | None:
    """Extract text output from a Langfuse observation (e.g. GENERATION)."""
    d = _obs_to_dict(obs)
    if not d:
        return None
    # Prefer direct output string
    out = d.get("output")
    if isinstance(out, str) and out.strip():
        return out.strip()
    if isinstance(out, list):
        # Message list (e.g. OpenAI format)
        for m in out:
            if isinstance(m, dict) and m.get("role") == "assistant" and "content" in m:
                c = m["content"]
                if isinstance(c, str):
                    return c.strip()
                if isinstance(c, list):
                    for p in c:
                        if isinstance(p, dict) and p.get("type") == "text" and "text" in p:
                            return p["text"].strip()
    return None


class LangfuseAdapter(Adapter):
    """Adapter that reads model output from a Langfuse trace (e.g. for evaluating prod traces)."""

    def __init__(
        self,
        trace_id: str,
        secret_key: str | None = None,
        public_key: str | None = None,
        host: str | None = None,
    ):
        """
        Initialize Langfuse adapter.

        Args:
            trace_id: Langfuse trace ID to read from.
            secret_key: Optional Langfuse secret key (default from env).
            public_key: Optional Langfuse public key (default from env).
            host: Optional Langfuse host (default from env).
        """
        self.trace_id = trace_id
        self._client = _get_langfuse_client(
            secret_key=secret_key,
            public_key=public_key,
            host=host,
        )

    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Read output from the Langfuse trace.

        Fetches the trace and its observations, finds the last GENERATION (or similar)
        observation, and returns its output as a string wrapped in GenerateResult
        with trace_id and observation_id for score linking.
        """
        trace_id = input_data.get("trace_id") or self.trace_id
        if not trace_id:
            return GenerateResult(output="", trace_id=None, observation_id=None)

        try:
            trace_raw = self._client.api.trace.get(trace_id)
        except Exception:
            return GenerateResult(output="", trace_id=trace_id, observation_id=None)

        # Trace object may have nested observations or we need to fetch them
        observations = getattr(trace_raw, "observations", None) or (
            trace_raw.get("observations") if isinstance(trace_raw, dict) else None
        )
        if not observations:
            try:
                obs_response = self._client.api.observations.get_many(trace_id=trace_id, limit=50)
                observations = (
                    getattr(obs_response, "data", obs_response)
                    if not isinstance(obs_response, list)
                    else obs_response
                )
            except Exception:
                observations = []

        if not isinstance(observations, list):
            observations = []

        # Prefer GENERATION type; take last one as the main output
        last_output = None
        last_observation_id = None
        for obs in reversed(observations):
            o = _obs_to_dict(obs)
            if not o:
                continue
            if o.get("type") == "GENERATION" or o.get("type") == "SPAN":
                out = _extract_output_from_observation(obs)
                if out is not None:
                    last_output = out
                    last_observation_id = o.get("id")
                    break

        if last_output is None:
            for obs in observations:
                out = _extract_output_from_observation(obs)
                if out is not None:
                    last_output = out
                    last_observation_id = _obs_to_dict(obs).get("id")
                    break

        return GenerateResult(
            output=last_output or "",
            trace_id=trace_id,
            observation_id=last_observation_id,
            metadata={"source": "langfuse_trace"},
        )
