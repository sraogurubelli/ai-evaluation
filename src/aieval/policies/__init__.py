"""Policy engine for guardrails (OPA-like policy-as-code).

This module provides a policy engine for evaluating guardrail rules
defined in YAML/JSON configuration files (policy-as-code approach).
"""

from aieval.policies.policy_engine import PolicyEngine
from aieval.policies.policy_loader import PolicyLoader
from aieval.policies.policy_validator import PolicyValidator
from aieval.policies.models import Policy, RuleConfig

__all__ = [
    "PolicyEngine",
    "PolicyLoader",
    "PolicyValidator",
    "Policy",
    "RuleConfig",
]
