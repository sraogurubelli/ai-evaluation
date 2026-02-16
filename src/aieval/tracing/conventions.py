"""OpenTelemetry / Langfuse attribute names and cost extraction helpers.

Use these constants when reading span attributes from OTel or Langfuse
to extract token counts and cost in a backend-agnostic way.
"""

from aieval.tracing.base import CostData

# OTel semantic conventions for LLM (and common variants)
ATTR_LLM_TOKEN_COUNT_INPUT = "llm.token_count.input"
ATTR_LLM_TOKEN_COUNT_OUTPUT = "llm.token_count.output"
ATTR_LLM_TOKENS_INPUT = "llm.tokens.input"
ATTR_LLM_TOKENS_OUTPUT = "llm.tokens.output"
ATTR_LLM_MODEL = "llm.model"
ATTR_LLM_PROVIDER = "llm.provider"
ATTR_LLM_COST = "llm.cost"

# Langfuse-style (if present in span attributes)
ATTR_TOTAL_COST = "total_cost"
ATTR_INPUT_TOKENS = "input_tokens"
ATTR_OUTPUT_TOKENS = "output_tokens"


def extract_cost_from_span_attributes(attrs: dict) -> CostData | None:
    """Build CostData from span attributes (OTel or Langfuse-style).

    Tries OTel convention keys first, then fallback names.
    Returns None if no token or cost data found.
    """
    if not attrs:
        return None

    def _int(key: str) -> int | None:
        v = attrs.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def _float(key: str) -> float | None:
        v = attrs.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _str(key: str) -> str | None:
        v = attrs.get(key)
        return str(v) if v is not None else None

    input_tokens = (
        _int(ATTR_LLM_TOKEN_COUNT_INPUT) or _int(ATTR_LLM_TOKENS_INPUT) or _int(ATTR_INPUT_TOKENS)
    )
    output_tokens = (
        _int(ATTR_LLM_TOKEN_COUNT_OUTPUT)
        or _int(ATTR_LLM_TOKENS_OUTPUT)
        or _int(ATTR_OUTPUT_TOKENS)
    )
    cost = _float(ATTR_LLM_COST) or _float(ATTR_TOTAL_COST)
    provider = _str(ATTR_LLM_PROVIDER)
    model = _str(ATTR_LLM_MODEL)

    if input_tokens is None and output_tokens is None and cost is None:
        return None

    total_tokens = None
    if input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    elif input_tokens is not None:
        total_tokens = input_tokens
    elif output_tokens is not None:
        total_tokens = output_tokens

    return CostData(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost=cost,
        provider=provider,
        model=model,
    )
