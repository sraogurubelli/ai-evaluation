"""Tests for LLM judge scorer."""

import pytest
from ai_evolution.scorers.llm_judge import LLMJudgeScorer


class TestLLMJudgeScorer:
    """Tests for LLMJudgeScorer."""
    
    def test_placeholder_implementation(self):
        """Test that placeholder implementation returns expected score."""
        scorer = LLMJudgeScorer()
        generated = "Generated output"
        expected = "Expected output"
        
        score = scorer.score(generated, expected, {})
        
        assert score.name == "llm_judge"
        assert score.value == 0.5  # Placeholder value
        assert "not yet implemented" in score.comment.lower()
    
    def test_custom_rubric(self):
        """Test scorer with custom rubric."""
        scorer = LLMJudgeScorer(rubric="Evaluate if the output is accurate.")
        generated = "Test"
        expected = "Test"
        
        score = scorer.score(generated, expected, {})
        
        assert score.metadata["rubric"] == "Evaluate if the output is accurate."
