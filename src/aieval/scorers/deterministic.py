"""Deterministic scorers for simple exact match, substring, and pattern matching.

These scorers provide fast, deterministic evaluation for common use cases
without requiring DeepDiff or LLM-as-judge calls. They wrap existing SDK
assertions into full Scorer implementations.
"""

import re
from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score
from aieval.sdk.assertions import (
    ExactMatchAssertion,
    ContainsAssertion,
    RegexAssertion,
)


class ExactMatchScorer(Scorer):
    """
    Scorer that checks for exact string equality.
    
    Returns 1.0 if the generated output exactly matches the expected value,
    0.0 otherwise. Comparison is done after stripping whitespace.
    
    Expected format examples:
        - {"exact": "hello world"}
        - {"value": "hello world"}
        - "hello world" (direct string)
    
    Configuration:
        - expected_field: Key to look for in expected dict (default: "exact")
    
    Example:
        scorer = ExactMatchScorer(
            name="exact_match",
            eval_id="exact_match.v1",
            expected_field="exact"
        )
    """
    
    def __init__(
        self,
        name: str = "exact_match",
        eval_id: str = "exact_match.v1",
        expected_field: str = "exact",
    ):
        """
        Initialize exact match scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            expected_field: Field name to extract from expected dict
        """
        super().__init__(name, eval_id)
        self.expected_field = expected_field
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score generated output against expected value.
        
        Args:
            generated: Generated output (any type, converted to string)
            expected: Expected output (dict with key or direct string)
            metadata: Additional metadata
            
        Returns:
            Score with value 1.0 (match) or 0.0 (no match)
        """
        # Extract expected value
        expected_value = None
        if isinstance(expected, dict):
            # Try configured field first, then fallbacks
            expected_value = expected.get(
                self.expected_field,
                expected.get("value", expected.get("exact"))
            )
        elif isinstance(expected, str):
            expected_value = expected
        else:
            expected_value = str(expected) if expected is not None else None
        
        # Handle missing expected
        if expected_value is None:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"No expected value found (looked for '{self.expected_field}' field)",
                metadata={**metadata, "expected_field": self.expected_field},
            )
        
        # Convert to strings and compare
        try:
            generated_str = str(generated).strip()
            expected_str = str(expected_value).strip()
            
            matches = generated_str == expected_str
            
            return Score(
                name=self.name,
                value=1.0 if matches else 0.0,
                eval_id=self.eval_id,
                comment=(
                    "Exact match" if matches
                    else f"Mismatch: expected '{expected_str[:100]}', got '{generated_str[:100]}'"
                ),
                metadata={
                    **metadata,
                    "expected": expected_str[:500],  # Limit metadata size
                    "generated": generated_str[:500],
                    "match": matches,
                },
            )
        except Exception as e:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Error during comparison: {str(e)}",
                metadata={**metadata, "error": str(e)},
            )


class ContainsScorer(Scorer):
    """
    Scorer that checks if output contains expected substring(s).
    
    Returns 1.0 if all required substrings are found, 0.0 if none are found,
    or a ratio (0.0-1.0) if require_all=False and some are found.
    
    Expected format examples:
        - {"contains": "keyword"}
        - {"contains": ["keyword1", "keyword2"]}
        - "keyword" (direct string)
        - ["keyword1", "keyword2"] (direct list)
    
    Configuration:
        - case_sensitive: Whether to do case-sensitive matching (default: False)
        - require_all: If True, all substrings must be present (default: True)
    
    Example:
        scorer = ContainsScorer(
            name="contains_keywords",
            eval_id="contains.v1",
            case_sensitive=False,
            require_all=True
        )
    """
    
    def __init__(
        self,
        name: str = "contains",
        eval_id: str = "contains.v1",
        case_sensitive: bool = False,
        require_all: bool = True,
    ):
        """
        Initialize contains scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            case_sensitive: Whether to do case-sensitive matching
            require_all: If True, all substrings must be present
        """
        super().__init__(name, eval_id)
        self.case_sensitive = case_sensitive
        self.require_all = require_all
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score generated output for substring presence.
        
        Args:
            generated: Generated output (any type, converted to string)
            expected: Expected substrings (dict, string, or list)
            metadata: Additional metadata
            
        Returns:
            Score with value 0.0-1.0 based on match ratio
        """
        # Extract substrings to check
        substrings = []
        if isinstance(expected, dict):
            contains_value = expected.get("contains", expected.get("value"))
            if isinstance(contains_value, str):
                substrings = [contains_value]
            elif isinstance(contains_value, list):
                substrings = [str(s) for s in contains_value]
            else:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment="Expected dict must have 'contains' field with string or list",
                    metadata=metadata,
                )
        elif isinstance(expected, str):
            substrings = [expected]
        elif isinstance(expected, list):
            substrings = [str(s) for s in expected]
        else:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Unsupported expected type: {type(expected)}",
                metadata=metadata,
            )
        
        if not substrings:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No substrings to check",
                metadata=metadata,
            )
        
        # Check each substring
        try:
            generated_str = str(generated)
            
            matches = []
            for substring in substrings:
                assertion = ContainsAssertion(
                    substring=substring,
                    case_sensitive=self.case_sensitive
                )
                found = assertion.check(generated_str)
                matches.append({
                    "substring": substring,
                    "found": found,
                })
            
            # Calculate score
            found_count = sum(1 for m in matches if m["found"])
            total_count = len(matches)
            
            if self.require_all:
                score_value = 1.0 if found_count == total_count else 0.0
            else:
                score_value = found_count / total_count if total_count > 0 else 0.0
            
            # Build comment
            found_list = [m["substring"] for m in matches if m["found"]]
            missing_list = [m["substring"] for m in matches if not m["found"]]
            
            if found_count == total_count:
                comment = f"All {total_count} substring(s) found"
            elif found_count == 0:
                comment = f"None of {total_count} substring(s) found"
            else:
                comment = f"{found_count}/{total_count} substring(s) found"
            
            return Score(
                name=self.name,
                value=score_value,
                eval_id=self.eval_id,
                comment=comment,
                metadata={
                    **metadata,
                    "matches": matches,
                    "found": found_list[:20],  # Limit list size
                    "missing": missing_list[:20],
                    "case_sensitive": self.case_sensitive,
                    "require_all": self.require_all,
                    "generated_preview": generated_str[:500],
                },
            )
        except Exception as e:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Error during contains check: {str(e)}",
                metadata={**metadata, "error": str(e)},
            )


class RegexMatchScorer(Scorer):
    """
    Scorer that checks if output matches expected regex pattern(s).
    
    Returns 1.0 if all required patterns match, 0.0 if none match,
    or a ratio (0.0-1.0) if require_all=False and some match.
    
    Expected format examples:
        - {"regex": r"\\d{4}"}
        - {"regex": [r"\\d{4}", r"[A-Z]+"]}
        - r"\\d{4}" (direct pattern string)
        - [r"\\d{4}", r"[A-Z]+"] (direct pattern list)
    
    Configuration:
        - require_all: If True, all patterns must match (default: True)
    
    Example:
        scorer = RegexMatchScorer(
            name="regex_format",
            eval_id="regex.v1",
            require_all=True
        )
    """
    
    def __init__(
        self,
        name: str = "regex",
        eval_id: str = "regex.v1",
        require_all: bool = True,
    ):
        """
        Initialize regex match scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            require_all: If True, all patterns must match
        """
        super().__init__(name, eval_id)
        self.require_all = require_all
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score generated output for regex pattern matches.
        
        Args:
            generated: Generated output (any type, converted to string)
            expected: Expected regex patterns (dict, string, or list)
            metadata: Additional metadata
            
        Returns:
            Score with value 0.0-1.0 based on match ratio
        """
        # Extract patterns to check
        patterns = []
        if isinstance(expected, dict):
            regex_value = expected.get("regex", expected.get("pattern", expected.get("value")))
            if isinstance(regex_value, str):
                patterns = [regex_value]
            elif isinstance(regex_value, list):
                patterns = [str(p) for p in regex_value]
            else:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment="Expected dict must have 'regex' field with string or list",
                    metadata=metadata,
                )
        elif isinstance(expected, str):
            patterns = [expected]
        elif isinstance(expected, list):
            patterns = [str(p) for p in expected]
        else:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Unsupported expected type: {type(expected)}",
                metadata=metadata,
            )
        
        if not patterns:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No patterns to check",
                metadata=metadata,
            )
        
        # Check each pattern
        try:
            generated_str = str(generated)
            
            matches = []
            for pattern_str in patterns:
                try:
                    # Compile and check pattern
                    assertion = RegexAssertion(pattern=pattern_str)
                    matched = assertion.check(generated_str)
                    
                    # Get sample matches (up to 3)
                    sample_matches = []
                    if matched:
                        regex = re.compile(pattern_str)
                        found_matches = regex.findall(generated_str)
                        sample_matches = found_matches[:3]
                    
                    matches.append({
                        "pattern": pattern_str,
                        "matched": matched,
                        "samples": sample_matches,
                    })
                except re.error as e:
                    matches.append({
                        "pattern": pattern_str,
                        "matched": False,
                        "error": f"Invalid regex: {str(e)}",
                    })
            
            # Calculate score
            matched_count = sum(1 for m in matches if m["matched"])
            total_count = len(matches)
            
            if self.require_all:
                score_value = 1.0 if matched_count == total_count else 0.0
            else:
                score_value = matched_count / total_count if total_count > 0 else 0.0
            
            # Build comment
            matched_list = [m["pattern"] for m in matches if m["matched"]]
            unmatched_list = [m["pattern"] for m in matches if not m["matched"]]
            
            if matched_count == total_count:
                comment = f"All {total_count} pattern(s) matched"
            elif matched_count == 0:
                comment = f"None of {total_count} pattern(s) matched"
            else:
                comment = f"{matched_count}/{total_count} pattern(s) matched"
            
            return Score(
                name=self.name,
                value=score_value,
                eval_id=self.eval_id,
                comment=comment,
                metadata={
                    **metadata,
                    "matches": matches,
                    "matched_patterns": matched_list[:20],  # Limit list size
                    "unmatched_patterns": unmatched_list[:20],
                    "require_all": self.require_all,
                    "generated_preview": generated_str[:500],
                },
            )
        except Exception as e:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Error during regex check: {str(e)}",
                metadata={**metadata, "error": str(e)},
            )
