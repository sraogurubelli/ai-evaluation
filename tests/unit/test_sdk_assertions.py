"""Tests for assertion system."""

import pytest
from ai_evolution.sdk.assertions import (
    ContainsAssertion,
    RegexAssertion,
    ExactMatchAssertion,
    JSONSchemaAssertion,
    FunctionAssertion,
    AssertionScorer,
)


class TestContainsAssertion:
    """Tests for ContainsAssertion."""
    
    def test_contains_case_insensitive(self):
        """Test case-insensitive contains."""
        assertion = ContainsAssertion("hello", case_sensitive=False)
        
        assert assertion.check("Hello World") is True
        assert assertion.check("HELLO WORLD") is True
        assert assertion.check("world") is False
    
    def test_contains_case_sensitive(self):
        """Test case-sensitive contains."""
        assertion = ContainsAssertion("Hello", case_sensitive=True)
        
        assert assertion.check("Hello World") is True
        assert assertion.check("HELLO WORLD") is False
    
    def test_contains_callable(self):
        """Test assertion is callable."""
        assertion = ContainsAssertion("test")
        
        assert assertion("This is a test") is True
        assert assertion("No match") is False


class TestRegexAssertion:
    """Tests for RegexAssertion."""
    
    def test_regex_match(self):
        """Test regex matching."""
        assertion = RegexAssertion(r"\d{4}-\d{2}-\d{2}")  # Date pattern
        
        assert assertion.check("2025-01-26") is True
        assert assertion.check("2025/01/26") is False
        assert assertion.check("not a date") is False


class TestExactMatchAssertion:
    """Tests for ExactMatchAssertion."""
    
    def test_exact_match(self):
        """Test exact matching."""
        assertion = ExactMatchAssertion("expected")
        
        assert assertion.check("expected") is True
        assert assertion.check("Expected") is False
        assert assertion.check("unexpected") is False
    
    def test_exact_match_normalized(self):
        """Test exact match with normalization."""
        assertion = ExactMatchAssertion("expected", normalize=True)
        
        assert assertion.check("expected") is True
        assert assertion.check("Expected") is True  # Normalized
        assert assertion.check("  expected  ") is True  # Trimmed


class TestJSONSchemaAssertion:
    """Tests for JSONSchemaAssertion."""
    
    def test_json_schema_valid(self):
        """Test valid JSON schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
            "required": ["name"],
        }
        
        assertion = JSONSchemaAssertion(schema)
        
        assert assertion.check({"name": "John", "age": 30}) is True
        assert assertion.check({"name": "John"}) is True  # age optional
    
    def test_json_schema_invalid(self):
        """Test invalid JSON schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        }
        
        assertion = JSONSchemaAssertion(schema)
        
        assert assertion.check({}) is False  # Missing required field
        assert assertion.check({"name": 123}) is False  # Wrong type


class TestFunctionAssertion:
    """Tests for FunctionAssertion."""
    
    def test_function_assertion(self):
        """Test function-based assertion."""
        def check_length(output, expected=None, **kwargs):
            return len(str(output)) > 10
        
        assertion = FunctionAssertion(check_length)
        
        assert assertion.check("This is a long string") is True
        assert assertion.check("short") is False


class TestAssertionScorer:
    """Tests for AssertionScorer."""
    
    def test_assertion_scorer_all_pass(self):
        """Test scorer when all assertions pass."""
        assertions = [
            ContainsAssertion("hello"),
            ContainsAssertion("world"),
        ]
        
        scorer = AssertionScorer(assertions)
        score = scorer.score("hello world", None, {})
        
        assert score.value == 1.0
    
    def test_assertion_scorer_partial_pass(self):
        """Test scorer when some assertions pass."""
        assertions = [
            ContainsAssertion("hello"),
            ContainsAssertion("world"),
        ]
        
        scorer = AssertionScorer(assertions)
        score = scorer.score("hello", None, {})
        
        assert score.value == 0.5  # 1 out of 2 passed
    
    def test_assertion_scorer_none_pass(self):
        """Test scorer when no assertions pass."""
        assertions = [
            ContainsAssertion("hello"),
            ContainsAssertion("world"),
        ]
        
        scorer = AssertionScorer(assertions)
        score = scorer.score("goodbye", None, {})
        
        assert score.value == 0.0
