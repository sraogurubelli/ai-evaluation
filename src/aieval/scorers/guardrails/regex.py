"""Regex-based rule scorer.

Allows users to define custom regex patterns for blocking or flagging content.
"""

import logging
import re
from typing import Any

from aieval.scorers.guardrails.base import GuardrailScorer
from aieval.core.types import Score

logger = logging.getLogger(__name__)


class RegexScorer(GuardrailScorer):
    """Detects content matching user-defined regex patterns.
    
    Useful for blocking specific patterns like:
    - Internal URLs or domains
    - Specific keywords or phrases
    - Format violations
    - Custom business rules
    """
    
    def __init__(
        self,
        name: str = "regex",
        eval_id: str = "regex.v1",
        threshold: float = 0.5,
        action: str = "block",
        patterns: list[str] | None = None,
    ):
        """
        Initialize regex scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            threshold: Threshold for pass/fail (0.0-1.0)
            action: Action to take if threshold exceeded
            patterns: List of regex patterns to match (strings or compiled regex)
        """
        super().__init__(name, eval_id, "regex", threshold, action)
        self.patterns = patterns or []
        self.compiled_patterns = []
        
        # Compile patterns
        for pattern in self.patterns:
            if isinstance(pattern, str):
                try:
                    self.compiled_patterns.append(re.compile(pattern))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            elif isinstance(pattern, re.Pattern):
                self.compiled_patterns.append(pattern)
            else:
                logger.warning(f"Invalid pattern type: {type(pattern)}")
    
    def score(
        self,
        generated: Any,
        expected: Any | None = None,
        metadata: dict[str, Any] = {},
    ) -> Score:
        """
        Score for regex matches.
        
        Args:
            generated: Text to check
            expected: Not used
            metadata: Additional metadata
            
        Returns:
            Score with value 0.0 (no matches) to 1.0 (matches found)
        """
        # Convert to string
        text = str(generated) if not isinstance(generated, str) else generated
        
        # Check for matches
        matches = []
        matched_patterns = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            pattern_matches = pattern.finditer(text)
            for match in pattern_matches:
                matches.append({
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "pattern": self.patterns[i] if i < len(self.patterns) else str(pattern),
                })
                if i not in matched_patterns:
                    matched_patterns.append(i)
        
        # Calculate score: any match = 1.0, no matches = 0.0
        score_value = 1.0 if matches else 0.0
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=(
                f"Regex matches found: {len(matches)} matches across {len(matched_patterns)} patterns"
                if matches
                else "No regex matches found"
            ),
            metadata={
                "matches": matches[:20],  # Limit to first 20 matches
                "match_count": len(matches),
                "matched_patterns": len(matched_patterns),
                "total_patterns": len(self.compiled_patterns),
                "text_length": len(text),
            },
        )
