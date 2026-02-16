"""Deterministic scorers for exact matching, substring matching, and regex matching."""

from typing import Any
import re

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class ExactMatchScorer(Scorer):
    """
    Scorer that checks if output exactly matches expected value.
    
    Performs case-insensitive, whitespace-normalized comparison by default.
    """
    
    def __init__(
        self,
        name: str = "exact_match",
        eval_id: str = "exact_match.v1",
        case_sensitive: bool = False,
        normalize_whitespace: bool = True,
    ):
        """
        Initialize exact match scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            case_sensitive: Whether comparison is case-sensitive
            normalize_whitespace: Whether to normalize whitespace before comparison
        """
        super().__init__(name=name, eval_id=eval_id)
        self.case_sensitive = case_sensitive
        self.normalize_whitespace = normalize_whitespace
    
    def _normalize(self, value: str) -> str:
        """Normalize string for comparison."""
        if not self.case_sensitive:
            value = value.lower()
        if self.normalize_whitespace:
            # Normalize whitespace: collapse multiple spaces, strip
            value = " ".join(value.split())
        return value.strip()
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score exact match.
        
        Args:
            generated: Generated output
            expected: Expected output (dict with "exact" or "value" key, or direct value)
            metadata: Additional metadata
            
        Returns:
            Score object (True if exact match, False otherwise)
        """
        generated_str = str(generated)
        
        # Extract expected value
        if isinstance(expected, dict):
            expected_value = expected.get("exact") or expected.get("value")
        else:
            expected_value = expected
        
        if expected_value is None:
            return Score(
                name=self.name,
                value=False,
                eval_id=self.eval_id,
                comment="No expected value provided",
                metadata=metadata,
            )
        
        expected_str = str(expected_value)
        
        # Normalize and compare
        generated_normalized = self._normalize(generated_str)
        expected_normalized = self._normalize(expected_str)
        
        is_match = generated_normalized == expected_normalized
        
        return Score(
            name=self.name,
            value=is_match,
            eval_id=self.eval_id,
            comment=f"Expected: {expected_str[:50]}{'...' if len(expected_str) > 50 else ''}, Got: {generated_str[:50]}{'...' if len(generated_str) > 50 else ''}",
            metadata={
                **metadata,
                "case_sensitive": self.case_sensitive,
                "normalize_whitespace": self.normalize_whitespace,
            },
        )


class ContainsScorer(Scorer):
    """
    Scorer that checks if output contains expected substring.
    
    Performs case-insensitive matching by default.
    """
    
    def __init__(
        self,
        name: str = "contains",
        eval_id: str = "contains.v1",
        case_sensitive: bool = False,
    ):
        """
        Initialize contains scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            case_sensitive: Whether matching is case-sensitive
        """
        super().__init__(name=name, eval_id=eval_id)
        self.case_sensitive = case_sensitive
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score contains check.
        
        Args:
            generated: Generated output
            expected: Expected substring (dict with "contains" key, or direct value)
            metadata: Additional metadata
            
        Returns:
            Score object (True if contains, False otherwise)
        """
        generated_str = str(generated)
        
        # Extract expected substring
        if isinstance(expected, dict):
            expected_substring = expected.get("contains") or expected.get("value")
        else:
            expected_substring = expected
        
        if expected_substring is None:
            return Score(
                name=self.name,
                value=False,
                eval_id=self.eval_id,
                comment="No expected substring provided",
                metadata=metadata,
            )
        
        expected_str = str(expected_substring)
        
        # Compare
        if not self.case_sensitive:
            generated_str = generated_str.lower()
            expected_str = expected_str.lower()
        
        contains = expected_str in generated_str
        
        return Score(
            name=self.name,
            value=contains,
            eval_id=self.eval_id,
            comment=f"Looking for: '{expected_substring}'",
            metadata={
                **metadata,
                "case_sensitive": self.case_sensitive,
            },
        )


class RegexScorer(Scorer):
    """
    Scorer that checks if output matches a regex pattern.
    """
    
    def __init__(
        self,
        name: str = "regex",
        eval_id: str = "regex.v1",
        pattern: str | None = None,
    ):
        """
        Initialize regex scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            pattern: Regex pattern (can also be provided in expected dict)
        """
        super().__init__(name=name, eval_id=eval_id)
        self.pattern = pattern
        self._compiled_pattern: re.Pattern[str] | None = None
        if pattern:
            self._compiled_pattern = re.compile(pattern)
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score regex match.
        
        Args:
            generated: Generated output
            expected: Expected regex pattern (dict with "regex" key, or direct value)
            metadata: Additional metadata
            
        Returns:
            Score object (True if matches, False otherwise)
        """
        generated_str = str(generated)
        
        # Extract pattern
        pattern = self.pattern
        if pattern is None:
            if isinstance(expected, dict):
                pattern = expected.get("regex") or expected.get("pattern") or expected.get("value")
            else:
                pattern = str(expected) if expected else None
        
        if pattern is None:
            return Score(
                name=self.name,
                value=False,
                eval_id=self.eval_id,
                comment="No regex pattern provided",
                metadata=metadata,
            )
        
        # Compile pattern if needed
        if self._compiled_pattern is None or self.pattern != pattern:
            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                return Score(
                    name=self.name,
                    value=False,
                    eval_id=self.eval_id,
                    comment=f"Invalid regex pattern: {str(e)}",
                    metadata=metadata,
                )
        else:
            compiled_pattern = self._compiled_pattern
        
        # Match
        matches = bool(compiled_pattern.search(generated_str))
        
        return Score(
            name=self.name,
            value=matches,
            eval_id=self.eval_id,
            comment=f"Pattern: {pattern}",
            metadata={
                **metadata,
                "pattern": pattern,
            },
        )
