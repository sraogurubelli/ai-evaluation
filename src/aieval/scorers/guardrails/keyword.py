"""Keyword-based blocking scorer.

Simple keyword matching for blocking specific words or phrases.
"""

import logging
from typing import Any

from aieval.scorers.guardrails.base import GuardrailScorer
from aieval.core.types import Score

logger = logging.getLogger(__name__)


class KeywordScorer(GuardrailScorer):
    """Detects specific keywords or phrases in text.
    
    Useful for blocking:
    - Competitor names
    - Internal project names
    - Forbidden terms
    - Brand names
    """
    
    def __init__(
        self,
        name: str = "keyword",
        eval_id: str = "keyword.v1",
        threshold: float = 0.5,
        action: str = "block",
        keywords: list[str] | None = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize keyword scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            threshold: Threshold for pass/fail (0.0-1.0)
            action: Action to take if threshold exceeded
            keywords: List of keywords/phrases to match
            case_sensitive: Whether matching is case-sensitive
        """
        super().__init__(name, eval_id, "keyword", threshold, action)
        self.keywords = keywords or []
        self.case_sensitive = case_sensitive
    
    def score(
        self,
        generated: Any,
        expected: Any | None = None,
        metadata: dict[str, Any] = {},
    ) -> Score:
        """
        Score for keyword matches.
        
        Args:
            generated: Text to check
            expected: Not used
            metadata: Additional metadata
            
        Returns:
            Score with value 0.0 (no keywords) to 1.0 (keywords found)
        """
        # Convert to string
        text = str(generated) if not isinstance(generated, str) else generated
        
        if not self.case_sensitive:
            text = text.lower()
        
        # Find matches
        matches = []
        for keyword in self.keywords:
            search_keyword = keyword if self.case_sensitive else keyword.lower()
            if search_keyword in text:
                # Find all occurrences
                start = 0
                while True:
                    idx = text.find(search_keyword, start)
                    if idx == -1:
                        break
                    matches.append({
                        "keyword": keyword,
                        "position": idx,
                    })
                    start = idx + 1
        
        # Calculate score: any match = 1.0, no matches = 0.0
        score_value = 1.0 if matches else 0.0
        
        # Get unique matched keywords
        matched_keywords = list(set(m["keyword"] for m in matches))
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=(
                f"Keywords found: {', '.join(matched_keywords)}"
                if matches
                else "No keywords found"
            ),
            metadata={
                "matches": matches[:20],  # Limit to first 20 matches
                "match_count": len(matches),
                "matched_keywords": matched_keywords,
                "total_keywords": len(self.keywords),
                "text_length": len(text),
                "case_sensitive": self.case_sensitive,
            },
        )
