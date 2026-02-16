"""Tests for autoevals-style scorers."""

import pytest
import os
from unittest.mock import patch, MagicMock
from aieval.scorers.autoevals import (
    FactualityScorer,
    HelpfulnessScorer,
    LevenshteinScorer,
    BLUEScorer,
    EmbeddingSimilarityScorer,
    RAGRelevanceScorer,
)


class TestLevenshteinScorer:
    """Tests for Levenshtein scorer."""

    def test_perfect_match(self):
        """Test perfect string match."""
        scorer = LevenshteinScorer()
        generated = "Hello world"
        expected = "Hello world"

        score = scorer.score(generated, expected, {})

        assert score.name == "levenshtein"
        assert score.value == 1.0

    def test_partial_match(self):
        """Test partial string match."""
        scorer = LevenshteinScorer()
        generated = "Hello world"
        expected = "Hello there"

        score = scorer.score(generated, expected, {})

        assert 0.0 < score.value < 1.0

    def test_empty_strings(self):
        """Test scoring empty strings."""
        scorer = LevenshteinScorer()
        generated = ""
        expected = ""

        score = scorer.score(generated, expected, {})

        assert score.value == 1.0


class TestBLUEScorer:
    """Tests for BLEU scorer."""

    def test_perfect_match(self):
        """Test perfect match returns high score."""
        scorer = BLUEScorer()
        generated = "Hello world"
        expected = "Hello world"

        score = scorer.score(generated, expected, {})

        assert score.name == "bleu"
        assert score.value == 1.0

    def test_partial_match(self):
        """Test partial match."""
        scorer = BLUEScorer()
        generated = "Hello world"
        expected = "Hello there world"

        score = scorer.score(generated, expected, {})

        assert 0.0 < score.value < 1.0


class TestLLMJudgeScorers:
    """Tests for LLM-as-judge scorers."""

    @patch.dict(os.environ, {}, clear=True)
    def test_llm_scorer_no_api_key(self):
        """Test LLM scorer without API key."""
        scorer = FactualityScorer()
        generated = "Test"
        expected = "Test"

        score = scorer.score(generated, expected, {})

        assert score.value == 0.0
        assert "error" in score.metadata
