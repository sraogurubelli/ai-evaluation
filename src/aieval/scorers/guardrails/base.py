"""Base guardrail scorer interface.

Guardrail scorers extend the Scorer interface with additional capabilities:
- Pass/fail evaluation (not just scoring)
- Block/warn/log actions
- Threshold-based decisions
- Real-time validation support
"""

from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class GuardrailScorer(Scorer):
    """Base class for guardrail scorers (safety checks).
    
    Guardrail scorers evaluate outputs for safety issues like:
    - Hallucination
    - Prompt injection
    - Toxicity
    - PII leakage
    - Sensitive data exposure
    
    They can be used in:
    1. Offline experiments (as regular scorers)
    2. Real-time validation (via validation endpoints)
    """
    
    def __init__(
        self,
        name: str,
        eval_id: str,
        check_type: str,
        threshold: float = 0.5,
        action: str = "warn",
    ):
        """
        Initialize guardrail scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            check_type: Type of check (hallucination, prompt_injection, etc.)
            threshold: Threshold for pass/fail (0.0-1.0)
            action: Action to take if threshold exceeded ("block", "warn", "log")
        """
        super().__init__(name, eval_id)
        self.check_type = check_type
        self.threshold = threshold
        self.action = action
    
    def score(
        self,
        generated: Any,
        expected: Any | None = None,
        metadata: dict[str, Any] = {},
    ) -> Score:
        """
        Score generated output for safety issues.
        
        Args:
            generated: Generated output (text, YAML, etc.)
            expected: Expected output (optional, for hallucination checks)
            metadata: Additional metadata (context, prompt, etc.)
            
        Returns:
            Score object with value (0.0 = safe, 1.0 = unsafe)
        """
        raise NotImplementedError("Subclasses must implement score()")
    
    def should_block(self, score_value: float) -> bool:
        """Determine if request should be blocked based on score."""
        return self.action == "block" and score_value >= self.threshold
    
    def passed(self, score_value: float) -> bool:
        """Determine if check passed (score below threshold)."""
        return score_value < self.threshold
    
    def get_action(self, score_value: float) -> str:
        """Get action to take based on score."""
        if self.should_block(score_value):
            return "block"
        elif score_value >= self.threshold:
            return self.action  # warn or log
        else:
            return "allow"
