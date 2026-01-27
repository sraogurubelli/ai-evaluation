"""Assertion system for granular evaluation checks (OpenAI Evals style).

Assertions provide fine-grained checks that can be combined into scorers.
This is similar to OpenAI Evals' assertion system and Promptfoo's assertions.
"""

from typing import Any, Callable
from abc import ABC, abstractmethod


class Assertion(ABC):
    """
    Base assertion interface.
    
    An assertion is a single check that returns True/False.
    Multiple assertions can be combined into a scorer.
    
    Example:
        class ContainsAssertion(Assertion):
            def __init__(self, substring: str):
                self.substring = substring
            
            def check(self, output: str, expected: dict[str, Any] | None = None) -> bool:
                return self.substring.lower() in output.lower()
    """
    
    @abstractmethod
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Check if assertion passes.
        
        Args:
            output: Generated output
            expected: Expected values (optional)
            **kwargs: Additional context
        
        Returns:
            True if assertion passes, False otherwise
        """
        pass
    
    def __call__(self, output: Any, expected: dict[str, Any] | None = None, **kwargs: Any) -> bool:
        """Make assertion callable."""
        return self.check(output, expected, **kwargs)


class ContainsAssertion(Assertion):
    """Check if output contains a substring."""
    
    def __init__(self, substring: str, case_sensitive: bool = False):
        """
        Initialize contains assertion.
        
        Args:
            substring: Substring to search for
            case_sensitive: Whether to do case-sensitive matching
        """
        self.substring = substring
        self.case_sensitive = case_sensitive
    
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Check if output contains substring."""
        output_str = str(output)
        if not self.case_sensitive:
            output_str = output_str.lower()
            substring = self.substring.lower()
        else:
            substring = self.substring
        return substring in output_str


class RegexAssertion(Assertion):
    """Check if output matches a regex pattern."""
    
    def __init__(self, pattern: str):
        """
        Initialize regex assertion.
        
        Args:
            pattern: Regex pattern to match
        """
        import re
        self.pattern = pattern
        self.regex = re.compile(pattern)  # noqa: W605
    
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Check if output matches regex."""
        return bool(self.regex.search(str(output)))


class ExactMatchAssertion(Assertion):
    """Check if output exactly matches expected value."""
    
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Check if output exactly matches expected."""
        if expected is None:
            return False
        expected_value = expected.get("exact", expected.get("value"))
        if expected_value is None:
            return False
        return str(output).strip() == str(expected_value).strip()


class JSONSchemaAssertion(Assertion):
    """Check if output is valid JSON matching a schema."""
    
    def __init__(self, schema: dict[str, Any]):
        """
        Initialize JSON schema assertion.
        
        Args:
            schema: JSON schema to validate against
        """
        self.schema = schema
    
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Check if output matches JSON schema."""
        import json
        from jsonschema import validate, ValidationError
        
        try:
            # Parse output as JSON
            if isinstance(output, str):
                parsed = json.loads(output)
            else:
                parsed = output
            
            # Validate against schema
            validate(instance=parsed, schema=self.schema)
            return True
        except (json.JSONDecodeError, ValidationError):
            return False


class FunctionAssertion(Assertion):
    """Assertion that uses a custom function."""
    
    def __init__(self, func: Callable[[Any, dict[str, Any] | None], bool], name: str = "custom"):
        """
        Initialize function assertion.
        
        Args:
            func: Function that takes (output, expected) and returns bool
            name: Name for the assertion
        """
        self.func = func
        self.name = name
    
    def check(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        """Check using custom function."""
        return self.func(output, expected, **kwargs)


class AssertionScorer:
    """
    Scorer that combines multiple assertions.
    
    This allows you to create scorers from multiple assertions,
    similar to OpenAI Evals and Promptfoo.
    
    Example:
        scorer = AssertionScorer(
            name="quality_check",
            assertions=[
                ContainsAssertion("success"),
                RegexAssertion(r"\d+"),
                JSONSchemaAssertion({"type": "object"}),
            ],
        )
    """
    
    def __init__(
        self,
        name: str,
        eval_id: str,
        assertions: list[Assertion],
        require_all: bool = True,
    ):
        """
        Initialize assertion scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            assertions: List of assertions to check
            require_all: If True, all assertions must pass. If False, any assertion passing is enough.
        """
        self.name = name
        self.eval_id = eval_id
        self.assertions = assertions
        self.require_all = require_all
    
    def score(
        self,
        output: Any,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Score output using assertions.
        
        Args:
            output: Generated output
            expected: Expected values
            **kwargs: Additional context
        
        Returns:
            Dictionary with score and details
        """
        results = []
        for assertion in self.assertions:
            passed = assertion.check(output, expected, **kwargs)
            results.append({
                "assertion": type(assertion).__name__,
                "passed": passed,
            })
        
        if self.require_all:
            overall_passed = all(r["passed"] for r in results)
        else:
            overall_passed = any(r["passed"] for r in results)
        
        passed_count = sum(1 for r in results if r["passed"])
        
        return {
            "name": self.name,
            "eval_id": self.eval_id,
            "value": float(overall_passed),
            "comment": f"{passed_count}/{len(results)} assertions passed",
            "metadata": {
                "assertion_results": results,
                "require_all": self.require_all,
            },
        }
