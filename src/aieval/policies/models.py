"""Policy configuration models (Pydantic)."""

from typing import Any

from pydantic import BaseModel, Field


class RuleConfig(BaseModel):
    """Configuration for a single guardrail rule."""
    
    id: str = Field(..., description="Unique rule identifier")
    type: str = Field(..., description="Rule type (hallucination, prompt_injection, etc.)")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Threshold for pass/fail")
    action: str = Field(default="warn", description="Action: block, warn, or log")
    config: dict[str, Any] = Field(default_factory=dict, description="Rule-specific configuration")


class Policy(BaseModel):
    """Policy configuration (policy-as-code)."""
    
    name: str = Field(..., description="Policy name")
    version: str = Field(default="v1", description="Policy version")
    description: str | None = Field(None, description="Policy description")
    rules: list[RuleConfig] = Field(default_factory=list, description="List of rules in this policy")
    
    def get_enabled_rules(self) -> list[RuleConfig]:
        """Get only enabled rules."""
        return [rule for rule in self.rules if rule.enabled]
    
    def get_rule_by_id(self, rule_id: str) -> RuleConfig | None:
        """Get rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
