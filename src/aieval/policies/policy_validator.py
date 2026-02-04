"""Policy validator for syntax and semantic validation."""

import logging
from typing import Any

from aieval.policies.models import Policy, RuleConfig

logger = logging.getLogger(__name__)


class PolicyValidator:
    """Validates policy configuration."""
    
    # Valid rule types
    VALID_RULE_TYPES = {
        "hallucination",
        "prompt_injection",
        "toxicity",
        "pii",
        "sensitive_data",
        "regex",
        "keyword",
    }
    
    # Valid actions
    VALID_ACTIONS = {"block", "warn", "log"}
    
    @staticmethod
    def validate(policy: Policy) -> tuple[bool, list[str]]:
        """
        Validate policy configuration.
        
        Args:
            policy: Policy to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate policy name
        if not policy.name or not policy.name.strip():
            errors.append("Policy name is required")
        
        # Validate rules
        if not policy.rules:
            errors.append("Policy must have at least one rule")
        
        rule_ids = set()
        for i, rule in enumerate(policy.rules):
            rule_errors = PolicyValidator._validate_rule(rule, i)
            errors.extend(rule_errors)
            
            # Check for duplicate rule IDs
            if rule.id in rule_ids:
                errors.append(f"Duplicate rule ID: {rule.id}")
            rule_ids.add(rule.id)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_rule(rule: RuleConfig, index: int) -> list[str]:
        """Validate a single rule."""
        errors = []
        prefix = f"Rule[{index}] (id={rule.id}):"
        
        # Validate rule ID
        if not rule.id or not rule.id.strip():
            errors.append(f"{prefix} Rule ID is required")
        
        # Validate rule type
        if rule.type not in PolicyValidator.VALID_RULE_TYPES:
            errors.append(
                f"{prefix} Invalid rule type '{rule.type}'. "
                f"Valid types: {', '.join(PolicyValidator.VALID_RULE_TYPES)}"
            )
        
        # Validate threshold
        if not (0.0 <= rule.threshold <= 1.0):
            errors.append(f"{prefix} Threshold must be between 0.0 and 1.0")
        
        # Validate action
        if rule.action not in PolicyValidator.VALID_ACTIONS:
            errors.append(
                f"{prefix} Invalid action '{rule.action}'. "
                f"Valid actions: {', '.join(PolicyValidator.VALID_ACTIONS)}"
            )
        
        # Type-specific validation
        if rule.type == "regex" and "patterns" not in rule.config:
            errors.append(f"{prefix} Regex rule requires 'patterns' in config")
        
        if rule.type == "keyword" and "keywords" not in rule.config:
            errors.append(f"{prefix} Keyword rule requires 'keywords' in config")
        
        return errors
