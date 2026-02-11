"""Tests for deterministic scorers."""

import pytest
from aieval.scorers.deterministic import (
    ExactMatchScorer,
    ContainsScorer,
    RegexMatchScorer,
)


# ============================================================================
# ExactMatchScorer Tests
# ============================================================================

def test_exact_match_scorer_success():
    """Test exact match scorer with matching strings."""
    scorer = ExactMatchScorer()
    
    generated = "hello world"
    expected = {"exact": "hello world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "exact_match"
    assert score.value == 1.0
    assert "Exact match" in score.comment
    assert score.metadata["match"] is True


def test_exact_match_scorer_fail():
    """Test exact match scorer with non-matching strings."""
    scorer = ExactMatchScorer()
    
    generated = "hello world"
    expected = {"exact": "goodbye world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "exact_match"
    assert score.value == 0.0
    assert "Mismatch" in score.comment
    assert score.metadata["match"] is False


def test_exact_match_scorer_whitespace_handling():
    """Test exact match scorer strips whitespace."""
    scorer = ExactMatchScorer()
    
    generated = "  hello world  "
    expected = {"exact": "hello world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0
    assert score.metadata["match"] is True


def test_exact_match_scorer_case_sensitive():
    """Test exact match scorer is case-sensitive."""
    scorer = ExactMatchScorer()
    
    generated = "Hello World"
    expected = {"exact": "hello world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0  # Case mismatch


def test_exact_match_scorer_string_expected():
    """Test exact match scorer with direct string expected."""
    scorer = ExactMatchScorer()
    
    generated = "test"
    expected = "test"
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_exact_match_scorer_value_field():
    """Test exact match scorer with 'value' field."""
    scorer = ExactMatchScorer()
    
    generated = "test"
    expected = {"value": "test"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_exact_match_scorer_custom_field():
    """Test exact match scorer with custom expected field."""
    scorer = ExactMatchScorer(expected_field="custom")
    
    generated = "test"
    expected = {"custom": "test"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_exact_match_scorer_missing_expected():
    """Test exact match scorer with missing expected field."""
    scorer = ExactMatchScorer()
    
    generated = "test"
    expected = {"wrong_field": "test"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "No expected value found" in score.comment


def test_exact_match_scorer_type_conversion():
    """Test exact match scorer converts types to strings."""
    scorer = ExactMatchScorer()
    
    generated = 123
    expected = {"exact": "123"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


# ============================================================================
# ContainsScorer Tests
# ============================================================================

def test_contains_scorer_single_match():
    """Test contains scorer with single matching substring."""
    scorer = ContainsScorer()
    
    generated = "The quick brown fox jumps over the lazy dog"
    expected = {"contains": "brown fox"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "contains"
    assert score.value == 1.0
    assert "All 1 substring(s) found" in score.comment


def test_contains_scorer_single_no_match():
    """Test contains scorer with single non-matching substring."""
    scorer = ContainsScorer()
    
    generated = "The quick brown fox"
    expected = {"contains": "lazy dog"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "None of 1 substring(s) found" in score.comment


def test_contains_scorer_case_insensitive():
    """Test contains scorer is case-insensitive by default."""
    scorer = ContainsScorer(case_sensitive=False)
    
    generated = "Hello World"
    expected = {"contains": "hello world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_contains_scorer_case_sensitive():
    """Test contains scorer with case sensitivity enabled."""
    scorer = ContainsScorer(case_sensitive=True)
    
    generated = "Hello World"
    expected = {"contains": "hello world"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0  # Case mismatch


def test_contains_scorer_multiple_all_found():
    """Test contains scorer with multiple substrings, all found."""
    scorer = ContainsScorer(require_all=True)
    
    generated = "The quick brown fox jumps over the lazy dog"
    expected = {"contains": ["quick", "fox", "lazy"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0
    assert "All 3 substring(s) found" in score.comment
    assert len(score.metadata["found"]) == 3


def test_contains_scorer_multiple_some_found():
    """Test contains scorer with multiple substrings, some found."""
    scorer = ContainsScorer(require_all=True)
    
    generated = "The quick brown fox"
    expected = {"contains": ["quick", "fox", "lazy"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0  # require_all=True
    assert "2/3 substring(s) found" in score.comment


def test_contains_scorer_multiple_any_mode():
    """Test contains scorer with require_all=False."""
    scorer = ContainsScorer(require_all=False)
    
    generated = "The quick brown fox"
    expected = {"contains": ["quick", "fox", "lazy"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == pytest.approx(0.667, abs=0.01)  # 2/3
    assert "2/3 substring(s) found" in score.comment


def test_contains_scorer_string_expected():
    """Test contains scorer with direct string expected."""
    scorer = ContainsScorer()
    
    generated = "hello world"
    expected = "world"
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_contains_scorer_list_expected():
    """Test contains scorer with direct list expected."""
    scorer = ContainsScorer()
    
    generated = "hello world"
    expected = ["hello", "world"]
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_contains_scorer_empty_expected():
    """Test contains scorer with empty expected."""
    scorer = ContainsScorer()
    
    generated = "hello world"
    expected = {"contains": []}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "No substrings to check" in score.comment


def test_contains_scorer_metadata():
    """Test contains scorer includes detailed metadata."""
    scorer = ContainsScorer()
    
    generated = "The quick brown fox"
    expected = {"contains": ["quick", "lazy"]}
    
    score = scorer.score(generated, expected, {})
    
    assert "matches" in score.metadata
    assert "found" in score.metadata
    assert "missing" in score.metadata
    assert score.metadata["case_sensitive"] is False
    assert score.metadata["require_all"] is True


# ============================================================================
# RegexMatchScorer Tests
# ============================================================================

def test_regex_scorer_single_match():
    """Test regex scorer with single matching pattern."""
    scorer = RegexMatchScorer()
    
    generated = "Version 1.2.3"
    expected = {"regex": r"\d+\.\d+\.\d+"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "regex"
    assert score.value == 1.0
    assert "All 1 pattern(s) matched" in score.comment


def test_regex_scorer_single_no_match():
    """Test regex scorer with single non-matching pattern."""
    scorer = RegexMatchScorer()
    
    generated = "No version here"
    expected = {"regex": r"\d+\.\d+\.\d+"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "None of 1 pattern(s) matched" in score.comment


def test_regex_scorer_multiple_all_match():
    """Test regex scorer with multiple patterns, all matching."""
    scorer = RegexMatchScorer(require_all=True)
    
    generated = "Version 1.2.3 released on 2024-01-15"
    expected = {"regex": [r"\d+\.\d+\.\d+", r"\d{4}-\d{2}-\d{2}"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0
    assert "All 2 pattern(s) matched" in score.comment


def test_regex_scorer_multiple_some_match():
    """Test regex scorer with multiple patterns, some matching."""
    scorer = RegexMatchScorer(require_all=True)
    
    generated = "Version 1.2.3"
    expected = {"regex": [r"\d+\.\d+\.\d+", r"\d{4}-\d{2}-\d{2}"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0  # require_all=True
    assert "1/2 pattern(s) matched" in score.comment


def test_regex_scorer_multiple_any_mode():
    """Test regex scorer with require_all=False."""
    scorer = RegexMatchScorer(require_all=False)
    
    generated = "Version 1.2.3"
    expected = {"regex": [r"\d+\.\d+\.\d+", r"\d{4}-\d{2}-\d{2}"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.5  # 1/2
    assert "1/2 pattern(s) matched" in score.comment


def test_regex_scorer_string_expected():
    """Test regex scorer with direct string pattern."""
    scorer = RegexMatchScorer()
    
    generated = "test123"
    expected = r"\d+"
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_regex_scorer_list_expected():
    """Test regex scorer with direct list of patterns."""
    scorer = RegexMatchScorer()
    
    generated = "test123"
    expected = [r"test", r"\d+"]
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_regex_scorer_invalid_pattern():
    """Test regex scorer handles invalid regex pattern gracefully."""
    scorer = RegexMatchScorer()
    
    generated = "test"
    expected = {"regex": r"[invalid("}  # Invalid regex
    
    score = scorer.score(generated, expected, {})
    
    # Should handle error gracefully
    assert score.value == 0.0
    assert "matches" in score.metadata
    assert "error" in str(score.metadata["matches"][0]).lower()


def test_regex_scorer_sample_matches():
    """Test regex scorer includes sample matches in metadata."""
    scorer = RegexMatchScorer()
    
    generated = "v1.2.3 and v4.5.6 and v7.8.9"
    expected = {"regex": r"v\d+\.\d+\.\d+"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0
    assert "matches" in score.metadata
    assert len(score.metadata["matches"][0]["samples"]) > 0


def test_regex_scorer_pattern_field():
    """Test regex scorer supports 'pattern' field."""
    scorer = RegexMatchScorer()
    
    generated = "test123"
    expected = {"pattern": r"\d+"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_regex_scorer_empty_expected():
    """Test regex scorer with empty expected."""
    scorer = RegexMatchScorer()
    
    generated = "test"
    expected = {"regex": []}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "No patterns to check" in score.comment


def test_regex_scorer_metadata():
    """Test regex scorer includes detailed metadata."""
    scorer = RegexMatchScorer()
    
    generated = "Version 1.2.3"
    expected = {"regex": [r"\d+\.\d+\.\d+", r"v\d+"]}
    
    score = scorer.score(generated, expected, {})
    
    assert "matches" in score.metadata
    assert "matched_patterns" in score.metadata
    assert "unmatched_patterns" in score.metadata
    assert "require_all" in score.metadata


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_exact_match_scorer_none_expected():
    """Test exact match scorer with None expected."""
    scorer = ExactMatchScorer()
    
    generated = "test"
    expected = None
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "No expected value found" in score.comment


def test_contains_scorer_unsupported_type():
    """Test contains scorer with unsupported expected type."""
    scorer = ContainsScorer()
    
    generated = "test"
    expected = 123  # Not a string, dict, or list
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "Unsupported expected type" in score.comment


def test_regex_scorer_unsupported_type():
    """Test regex scorer with unsupported expected type."""
    scorer = RegexMatchScorer()
    
    generated = "test"
    expected = 123  # Not a string, dict, or list
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.0
    assert "Unsupported expected type" in score.comment


def test_exact_match_scorer_metadata_preserved():
    """Test that input metadata is preserved in score."""
    scorer = ExactMatchScorer()
    
    generated = "test"
    expected = {"exact": "test"}
    metadata = {"test_id": "001", "entity_type": "pipeline"}
    
    score = scorer.score(generated, expected, metadata)
    
    assert score.metadata["test_id"] == "001"
    assert score.metadata["entity_type"] == "pipeline"


def test_contains_scorer_metadata_preserved():
    """Test that input metadata is preserved in score."""
    scorer = ContainsScorer()
    
    generated = "test"
    expected = {"contains": "test"}
    metadata = {"test_id": "002"}
    
    score = scorer.score(generated, expected, metadata)
    
    assert score.metadata["test_id"] == "002"


def test_regex_scorer_metadata_preserved():
    """Test that input metadata is preserved in score."""
    scorer = RegexMatchScorer()
    
    generated = "test123"
    expected = {"regex": r"\d+"}
    metadata = {"test_id": "003"}
    
    score = scorer.score(generated, expected, metadata)
    
    assert score.metadata["test_id"] == "003"


# ============================================================================
# Real-World Usage Patterns
# ============================================================================

def test_contains_scorer_keywords_in_text():
    """Test contains scorer for keyword matching use case."""
    scorer = ContainsScorer(case_sensitive=False, require_all=True)
    
    generated = "Deploy pipeline to production environment with CD stage"
    expected = {"contains": ["pipeline", "production", "CD"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_regex_scorer_version_formats():
    """Test regex scorer for version number matching."""
    scorer = RegexMatchScorer()
    
    generated = "Release v1.2.3-beta"
    expected = {"regex": r"v\d+\.\d+\.\d+(-\w+)?"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_exact_match_scorer_yaml_identifiers():
    """Test exact match for YAML identifier validation."""
    scorer = ExactMatchScorer(expected_field="identifier")
    
    generated = "my_pipeline_v1"
    expected = {"identifier": "my_pipeline_v1"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0


def test_contains_scorer_multiple_partial_any():
    """Test contains scorer with partial matches in any mode."""
    scorer = ContainsScorer(require_all=False)
    
    generated = "Only has keyword1 and keyword2"
    expected = {"contains": ["keyword1", "keyword2", "keyword3", "keyword4"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 0.5  # 2/4 found


def test_regex_scorer_complex_patterns():
    """Test regex scorer with complex patterns."""
    scorer = RegexMatchScorer(require_all=True)
    
    generated = """
    Email: user@example.com
    Phone: 555-1234
    URL: https://example.com
    """
    expected = {
        "regex": [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\d{3}-\d{4}",  # Phone
            r"https?://[^\s]+",  # URL
        ]
    }
    
    score = scorer.score(generated, expected, {})
    
    assert score.value == 1.0
    assert len(score.metadata["matched_patterns"]) == 3


# ============================================================================
# Scorer Configuration Tests
# ============================================================================

def test_exact_match_scorer_custom_name_and_id():
    """Test exact match scorer with custom name and eval_id."""
    scorer = ExactMatchScorer(
        name="custom_exact",
        eval_id="custom.v1",
    )
    
    generated = "test"
    expected = {"exact": "test"}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "custom_exact"
    assert score.eval_id == "custom.v1"


def test_contains_scorer_custom_config():
    """Test contains scorer with custom configuration."""
    scorer = ContainsScorer(
        name="keywords_check",
        eval_id="keywords.v2",
        case_sensitive=True,
        require_all=False,
    )
    
    generated = "TEST"
    expected = {"contains": ["TEST", "missing"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "keywords_check"
    assert score.eval_id == "keywords.v2"
    assert score.value == 0.5  # 1/2


def test_regex_scorer_custom_config():
    """Test regex scorer with custom configuration."""
    scorer = RegexMatchScorer(
        name="pattern_check",
        eval_id="pattern.v2",
        require_all=False,
    )
    
    generated = "123"
    expected = {"regex": [r"\d+", r"[a-z]+"]}
    
    score = scorer.score(generated, expected, {})
    
    assert score.name == "pattern_check"
    assert score.eval_id == "pattern.v2"
    assert score.value == 0.5  # 1/2


# ============================================================================
# Metadata Size Limiting Tests
# ============================================================================

def test_exact_match_scorer_truncates_large_strings():
    """Test exact match scorer truncates large strings in metadata."""
    scorer = ExactMatchScorer()
    
    large_text = "x" * 1000
    generated = large_text
    expected = {"exact": "different"}
    
    score = scorer.score(generated, expected, {})
    
    # Metadata should be truncated to 500 chars
    assert len(score.metadata["generated"]) <= 500
    assert len(score.metadata["expected"]) <= 500


def test_contains_scorer_limits_match_lists():
    """Test contains scorer limits match list sizes."""
    scorer = ContainsScorer()
    
    # Create 25 substrings
    substrings = [f"word{i}" for i in range(25)]
    generated = " ".join(substrings)
    expected = {"contains": substrings}
    
    score = scorer.score(generated, expected, {})
    
    # Should limit to 20 items
    assert len(score.metadata["found"]) <= 20


def test_regex_scorer_limits_pattern_lists():
    """Test regex scorer limits pattern list sizes."""
    scorer = RegexMatchScorer()
    
    # Create 25 patterns
    patterns = [rf"word{i}" for i in range(25)]
    generated = "word0 word1 word2"  # Only first 3 match
    expected = {"regex": patterns}
    
    score = scorer.score(generated, expected, {})
    
    # Should limit to 20 items
    assert len(score.metadata["unmatched_patterns"]) <= 20
