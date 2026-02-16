"""Guardrail SDK functions for programmatic access."""

import logging
from typing import Any

from aieval.policies.policy_engine import PolicyEngine
from aieval.policies.policy_loader import PolicyLoader
from aieval.policies.policy_validator import PolicyValidator
from aieval.policies.models import Policy

logger = logging.getLogger(__name__)

# Global policy engine instance
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get or create global policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


async def validate_prompt(
    prompt: str,
    task_id: str | None = None,
    policy_name: str | None = None,
    rule_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate a prompt before sending to LLM.

    Args:
        prompt: Prompt text to validate
        task_id: Optional task context
        policy_name: Policy name (if None, uses all policies)
        rule_ids: Specific rule IDs to check
        metadata: Additional metadata

    Returns:
        Validation result dictionary
    """
    engine = get_policy_engine()
    result = engine.validate(
        text=prompt,
        policy_name=policy_name,
        rule_ids=rule_ids,
        metadata=metadata or {},
    )
    return result.to_dict()


async def validate_response(
    prompt: str,
    response: str,
    context: str | None = None,
    task_id: str | None = None,
    policy_name: str | None = None,
    rule_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate an LLM response.

    Args:
        prompt: Original prompt
        response: Response text to validate
        context: RAG context (for hallucination checks)
        task_id: Optional task context
        policy_name: Policy name (if None, uses all policies)
        rule_ids: Specific rule IDs to check
        metadata: Additional metadata

    Returns:
        Validation result dictionary
    """
    engine = get_policy_engine()
    metadata = metadata or {}
    metadata["context"] = context
    metadata["prompt"] = prompt

    result = engine.validate(
        text=response,
        policy_name=policy_name,
        rule_ids=rule_ids,
        metadata=metadata,
    )
    return result.to_dict()


def load_policy(
    file_path: str | None = None,
    policy_yaml: str | None = None,
    name: str | None = None,
) -> Policy:
    """
    Load a policy from file or YAML string.

    Args:
        file_path: Path to policy YAML file
        policy_yaml: Policy YAML content as string
        name: Optional name override

    Returns:
        Policy object
    """
    loader = PolicyLoader()

    if file_path:
        policy = loader.load_from_file(file_path)
    elif policy_yaml:
        policy = loader.load_from_string(policy_yaml, format="yaml")
    else:
        raise ValueError("Either file_path or policy_yaml must be provided")

    # Load into global policy engine
    engine = get_policy_engine()
    policy_name = name or policy.name
    engine.load_policy(policy, name=policy_name)

    return policy


def validate_policy_config(
    policy_yaml: str | None = None,
    policy: Policy | None = None,
) -> dict[str, Any]:
    """
    Validate policy configuration.

    Args:
        policy_yaml: Policy YAML content
        policy: Policy object (if already loaded)

    Returns:
        Validation result with 'valid' and 'errors' keys
    """
    validator = PolicyValidator()

    if policy is None:
        if policy_yaml is None:
            raise ValueError("Either policy or policy_yaml must be provided")
        loader = PolicyLoader()
        policy = loader.load_from_string(policy_yaml, format="yaml")

    is_valid, errors = validator.validate(policy)

    return {
        "valid": is_valid,
        "errors": errors,
        "rule_count": len(policy.rules),
        "enabled_rule_count": len(policy.get_enabled_rules()),
    }


# Export guardrail scorers for use in experiments
from aieval.scorers.guardrails import (
    GuardrailScorer,
    HallucinationScorer,
    PromptInjectionScorer,
    ToxicityScorer,
    PIIScorer,
    SensitiveDataScorer,
    RegexScorer,
    KeywordScorer,
)

__all__ = [
    "validate_prompt",
    "validate_response",
    "load_policy",
    "validate_policy_config",
    "get_policy_engine",
    # Scorers
    "GuardrailScorer",
    "HallucinationScorer",
    "PromptInjectionScorer",
    "ToxicityScorer",
    "PIIScorer",
    "SensitiveDataScorer",
    "RegexScorer",
    "KeywordScorer",
]
