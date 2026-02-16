"""Policy engine for evaluating guardrail rules (OPA-like).

Evaluates policies against text inputs and returns validation results.
"""

import logging
from typing import Any

from aieval.policies.models import Policy, RuleConfig
from aieval.scorers.guardrails.base import GuardrailScorer
from aieval.scorers.guardrails.hallucination import HallucinationScorer
from aieval.scorers.guardrails.prompt_injection import PromptInjectionScorer
from aieval.scorers.guardrails.toxicity import ToxicityScorer
from aieval.scorers.guardrails.pii import PIIScorer
from aieval.scorers.guardrails.sensitive_data import SensitiveDataScorer
from aieval.scorers.guardrails.regex import RegexScorer
from aieval.scorers.guardrails.keyword import KeywordScorer

logger = logging.getLogger(__name__)


class RuleResult:
    """Result from evaluating a single rule."""

    def __init__(
        self,
        rule_id: str,
        rule_type: str,
        passed: bool,
        score: float,
        action: str,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.passed = passed
        self.score = score
        self.action = action
        self.comment = comment
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type,
            "passed": self.passed,
            "score": self.score,
            "action": self.action,
            "comment": self.comment,
            "metadata": self.metadata,
        }


class ValidationResult:
    """Result from validating text against a policy."""

    def __init__(
        self,
        passed: bool,
        rule_results: list[RuleResult],
        blocked: bool = False,
    ):
        self.passed = passed
        self.rule_results = rule_results
        self.blocked = blocked

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "blocked": self.blocked,
            "rule_results": [r.to_dict() for r in self.rule_results],
        }


class PolicyEngine:
    """Policy evaluation engine (OPA-like)."""

    def __init__(self):
        """Initialize policy engine."""
        self.policies: dict[str, Policy] = {}

    def load_policy(self, policy: Policy, name: str | None = None) -> None:
        """
        Load a policy into the engine.

        Args:
            policy: Policy to load
            name: Optional name override (defaults to policy.name)
        """
        policy_name = name or policy.name
        self.policies[policy_name] = policy
        logger.info(f"Loaded policy: {policy_name} (version: {policy.version})")

    def get_policy(self, name: str) -> Policy | None:
        """Get policy by name."""
        return self.policies.get(name)

    def _create_scorer(self, rule: RuleConfig) -> GuardrailScorer | None:
        """Create scorer instance from rule configuration."""
        scorer_class = {
            "hallucination": HallucinationScorer,
            "prompt_injection": PromptInjectionScorer,
            "toxicity": ToxicityScorer,
            "pii": PIIScorer,
            "sensitive_data": SensitiveDataScorer,
            "regex": RegexScorer,
            "keyword": KeywordScorer,
        }.get(rule.type)

        if not scorer_class:
            logger.warning(f"Unknown rule type: {rule.type}")
            return None

        # Create scorer with rule configuration
        scorer_kwargs = {
            "name": rule.id,
            "eval_id": f"{rule.type}.{rule.id}",
            "threshold": rule.threshold,
            "action": rule.action,
        }

        # Add type-specific config
        if rule.type == "regex" and "patterns" in rule.config:
            scorer_kwargs["patterns"] = rule.config["patterns"]

        if rule.type == "keyword" and "keywords" in rule.config:
            scorer_kwargs["keywords"] = rule.config["keywords"]
            scorer_kwargs["case_sensitive"] = rule.config.get("case_sensitive", False)

        if rule.type == "toxicity" and "violation_types" in rule.config:
            scorer_kwargs["violation_types"] = rule.config["violation_types"]

        if rule.type == "pii" and "entities" in rule.config:
            scorer_kwargs["entities"] = rule.config["entities"]

        if rule.type == "pii" and "use_presidio" in rule.config:
            scorer_kwargs["use_presidio"] = rule.config["use_presidio"]

        if rule.type == "sensitive_data":
            if "hint" in rule.config:
                scorer_kwargs["hint"] = rule.config["hint"]
            if "examples" in rule.config:
                scorer_kwargs["examples"] = rule.config["examples"]

        try:
            return scorer_class(**scorer_kwargs)
        except Exception as e:
            logger.error(f"Failed to create scorer for rule {rule.id}: {e}")
            return None

    def validate(
        self,
        text: str,
        policy_name: str | None = None,
        rule_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate text against policy.

        Args:
            text: Text to validate
            policy_name: Policy name (if None, uses all policies)
            rule_ids: Specific rule IDs to check (if None, checks all enabled rules)
            metadata: Additional metadata (e.g., context for hallucination checks)

        Returns:
            ValidationResult
        """
        metadata = metadata or {}

        # Get policies to evaluate
        if policy_name:
            policies = [self.policies[policy_name]] if policy_name in self.policies else []
        else:
            policies = list(self.policies.values())

        if not policies:
            logger.warning("No policies found for validation")
            return ValidationResult(
                passed=True,
                rule_results=[],
                blocked=False,
            )

        # Collect rules to evaluate
        rules_to_check: list[tuple[Policy, RuleConfig]] = []
        for policy in policies:
            for rule in policy.get_enabled_rules():
                if rule_ids is None or rule.id in rule_ids:
                    rules_to_check.append((policy, rule))

        # Evaluate each rule
        rule_results: list[RuleResult] = []
        blocked = False

        for policy, rule in rules_to_check:
            scorer = self._create_scorer(rule)
            if not scorer:
                continue

            try:
                # Score the text
                score_obj = scorer.score(
                    generated=text,
                    expected=None,
                    metadata=metadata,
                )

                score_value = score_obj.value if isinstance(score_obj.value, (int, float)) else 0.0
                passed = scorer.passed(score_value)
                action = scorer.get_action(score_value)

                # Check if should block
                if action == "block":
                    blocked = True

                rule_result = RuleResult(
                    rule_id=rule.id,
                    rule_type=rule.type,
                    passed=passed,
                    score=score_value,
                    action=action,
                    comment=score_obj.comment,
                    metadata=score_obj.metadata,
                )
                rule_results.append(rule_result)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}", exc_info=True)
                rule_result = RuleResult(
                    rule_id=rule.id,
                    rule_type=rule.type,
                    passed=False,
                    score=1.0,  # Fail-safe: assume failure on error
                    action="block",
                    comment=f"Error evaluating rule: {e}",
                    metadata={"error": str(e)},
                )
                rule_results.append(rule_result)
                blocked = True

        # Overall result: passed if all rules passed and not blocked
        overall_passed = all(r.passed for r in rule_results) and not blocked

        return ValidationResult(
            passed=overall_passed,
            rule_results=rule_results,
            blocked=blocked,
        )
