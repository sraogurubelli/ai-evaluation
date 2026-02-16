"""Tests for scorers."""

import pytest
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer


def test_deepdiff_scorer_v1():
    """Test DeepDiff scorer v1."""
    scorer = DeepDiffScorer(version="v1")

    generated = {"key": "value"}
    expected = {"key": "value"}

    score = scorer.score(generated, expected, {})

    assert score.name == "deep_diff"
    assert score.value == 1.0  # Perfect match


def test_deepdiff_scorer_mismatch():
    """Test DeepDiff scorer with mismatch."""
    scorer = DeepDiffScorer(version="v1")

    generated = {"key": "value1"}
    expected = {"key": "value2"}

    score = scorer.score(generated, expected, {})

    assert score.name == "deep_diff"
    assert score.value < 1.0  # Not perfect match


def test_schema_validation_scorer_no_func():
    """Test schema validation scorer without validation function."""
    scorer = SchemaValidationScorer()

    score = scorer.score("test: yaml", None, {})

    assert score.value is True  # Passes if no validation function


def test_schema_validation_scorer_with_func():
    """Test schema validation scorer with validation function."""

    def validation_func(yaml_str):
        return {"valid": True, "errors": []}

    scorer = SchemaValidationScorer(validation_func=validation_func)

    score = scorer.score("test: yaml", None, {})

    assert score.value is True
