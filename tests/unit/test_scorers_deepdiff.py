"""Comprehensive tests for DeepDiff scorers."""

import pytest
import yaml
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.core.types import Score


class TestDeepDiffScorerV1:
    """Tests for DeepDiff scorer v1."""
    
    def test_perfect_match(self):
        """Test perfect match returns 1.0."""
        scorer = DeepDiffScorer(version="v1")
        generated = {"key": "value"}
        expected = {"key": "value"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.name == "deep_diff"
        assert score.value == 1.0
        assert score.comment == ""
    
    def test_partial_match(self):
        """Test partial match returns value between 0 and 1."""
        scorer = DeepDiffScorer(version="v1")
        generated = {"key": "value1"}
        expected = {"key": "value2"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.name == "deep_diff"
        assert 0.0 <= score.value < 1.0
    
    def test_yaml_string_input(self):
        """Test scoring with YAML string inputs."""
        scorer = DeepDiffScorer(version="v1")
        generated = "key: value1"
        expected = "key: value2"
        
        score = scorer.score(generated, expected, {})
        
        assert score.name == "deep_diff"
        assert 0.0 <= score.value <= 1.0
    
    def test_invalid_yaml_generated(self):
        """Test handling of invalid YAML in generated."""
        scorer = DeepDiffScorer(version="v1")
        generated = "invalid: yaml: : :"
        expected = {"key": "value"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.value == 0.0
        assert "Failed to parse generated YAML" in score.comment
    
    def test_expected_dict_with_yaml_key(self):
        """Test handling expected dict with 'yaml' key (index_csv format)."""
        scorer = DeepDiffScorer(version="v1")
        generated = {"key": "value"}
        expected = {"yaml": "key: value", "entity_type": "pipeline"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.value == 1.0


class TestDeepDiffScorerV2:
    """Tests for DeepDiff scorer v2."""
    
    def test_perfect_match(self):
        """Test perfect match returns 1.0."""
        scorer = DeepDiffScorer(version="v2")
        generated = {"key": "value"}
        expected = {"key": "value"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.value == 1.0


class TestDeepDiffScorerV3:
    """Tests for DeepDiff scorer v3."""
    
    def test_perfect_match(self):
        """Test perfect match returns 1.0."""
        scorer = DeepDiffScorer(version="v3")
        generated = {"key": "value"}
        expected = {"key": "value"}
        
        score = scorer.score(generated, expected, {})
        
        assert score.value == 1.0
