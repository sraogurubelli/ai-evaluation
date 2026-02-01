"""Tests for metric-specific scorers."""

import json
import pytest

from ai_evolution.scorers.metrics import (
    LatencyScorer,
    ToolCallScorer,
    TokenUsageScorer,
)
from ai_evolution.core.types import Score


class TestLatencyScorer:
    """Tests for LatencyScorer."""
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        scorer = LatencyScorer()
        
        assert scorer.name == "latency"
        assert scorer.eval_id == "latency.v1"
        assert scorer.max_latency_ms == 30000
    
    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        scorer = LatencyScorer(max_latency_ms=5000)
        
        assert scorer.max_latency_ms == 5000
    
    def test_score_under_threshold(self):
        """Test scoring when latency is under threshold."""
        scorer = LatencyScorer(max_latency_ms=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {"latency_ms": 3000}
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "latency"
        assert score.value == 1.0
        assert "3000ms" in score.comment
        assert score.metadata["latency_ms"] == 3000
        assert score.metadata["threshold_ms"] == 5000
    
    def test_score_over_threshold(self):
        """Test scoring when latency is over threshold."""
        scorer = LatencyScorer(max_latency_ms=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {"latency_ms": 7500}  # 50% over threshold
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "latency"
        # Should be 0.5 (linear decay: 1.0 - (7500-5000)/5000 = 0.5)
        assert score.value == 0.5
    
    def test_score_far_over_threshold(self):
        """Test scoring when latency is far over threshold."""
        scorer = LatencyScorer(max_latency_ms=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {"latency_ms": 15000}  # 200% over threshold
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "latency"
        # Should be 0.0 (way over threshold)
        assert score.value == 0.0
    
    def test_score_no_latency_data(self):
        """Test scoring when no latency data is present."""
        scorer = LatencyScorer()
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {}
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.value == 0.0
        assert "No latency data" in score.comment
    
    def test_extract_latency_from_root(self):
        """Test extracting latency from root level."""
        scorer = LatencyScorer()
        
        enriched_output = {"latency_ms": 1000}
        
        latency = scorer._extract_latency(enriched_output)
        
        assert latency == 1000


class TestToolCallScorer:
    """Tests for ToolCallScorer."""
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        scorer = ToolCallScorer()
        
        assert scorer.name == "tool_calls"
        assert scorer.eval_id == "tool_calls.v1"
        assert scorer.require_tools is False
    
    def test_init_require_tools(self):
        """Test initialization with require_tools."""
        scorer = ToolCallScorer(require_tools=True)
        
        assert scorer.require_tools is True
    
    def test_score_with_tools(self):
        """Test scoring when tools are called."""
        scorer = ToolCallScorer()
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "tools_called": [
                {"tool": "search", "parameters": {"query": "test"}},
                {"tool": "calculate", "parameters": {"expr": "2+2"}},
            ]
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "tool_calls"
        assert score.value == 1.0
        assert "search" in score.comment
        assert "calculate" in score.comment
        assert score.metadata["tool_count"] == 2
        assert score.metadata["tools_used"] is True
        assert len(score.metadata["tools_called"]) == 2
    
    def test_score_without_tools(self):
        """Test scoring when no tools are called."""
        scorer = ToolCallScorer()
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "tools_called": []
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "tool_calls"
        assert score.value == 1.0  # Still 1.0 when require_tools=False
        assert "No tools called" in score.comment
        assert score.metadata["tool_count"] == 0
        assert score.metadata["tools_used"] is False
    
    def test_score_require_tools_with_tools(self):
        """Test scoring with require_tools=True when tools are called."""
        scorer = ToolCallScorer(require_tools=True)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "tools_called": [{"tool": "search"}]
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.value == 1.0
    
    def test_score_require_tools_without_tools(self):
        """Test scoring with require_tools=True when no tools are called."""
        scorer = ToolCallScorer(require_tools=True)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "tools_called": []
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.value == 0.0
    
    def test_extract_tools_from_enriched_output(self):
        """Test extracting tools from enriched output."""
        scorer = ToolCallScorer()
        
        enriched_output = json.dumps({
            "tools_called": [{"tool": "test"}]
        })
        
        tools = scorer._extract_tools(enriched_output)
        
        assert len(tools) == 1
        assert tools[0]["tool"] == "test"
    
    def test_extract_tools_from_dict(self):
        """Test extracting tools from dict input."""
        scorer = ToolCallScorer()
        
        enriched_output = {
            "tools_called": [{"tool": "test"}]
        }
        
        tools = scorer._extract_tools(enriched_output)
        
        assert len(tools) == 1


class TestTokenUsageScorer:
    """Tests for TokenUsageScorer."""
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        scorer = TokenUsageScorer()
        
        assert scorer.name == "token_usage"
        assert scorer.eval_id == "token_usage.v1"
        assert scorer.max_tokens == 10000
    
    def test_init_custom_budget(self):
        """Test initialization with custom budget."""
        scorer = TokenUsageScorer(max_tokens=5000)
        
        assert scorer.max_tokens == 5000
    
    def test_score_under_budget(self):
        """Test scoring when token usage is under budget."""
        scorer = TokenUsageScorer(max_tokens=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {
                "total_tokens": 3000,
                "prompt_tokens": 1000,
                "completion_tokens": 2000
            }
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "token_usage"
        assert score.value == 1.0
        assert "3000" in score.comment
        assert score.metadata["total_tokens"] == 3000
        assert score.metadata["prompt_tokens"] == 1000
        assert score.metadata["completion_tokens"] == 2000
        assert score.metadata["token_budget"] == 5000
    
    def test_score_over_budget(self):
        """Test scoring when token usage is over budget."""
        scorer = TokenUsageScorer(max_tokens=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {
                "total_tokens": 7500,  # 50% over budget
                "prompt_tokens": 2500,
                "completion_tokens": 5000
            }
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "token_usage"
        # Should be 0.5 (linear decay: 1.0 - (7500-5000)/5000 = 0.5)
        assert score.value == 0.5
    
    def test_score_far_over_budget(self):
        """Test scoring when token usage is far over budget."""
        scorer = TokenUsageScorer(max_tokens=5000)
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {
                "total_tokens": 15000,  # 200% over budget
                "prompt_tokens": 5000,
                "completion_tokens": 10000
            }
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.name == "token_usage"
        # Should be 0.0 (way over budget)
        assert score.value == 0.0
    
    def test_score_no_token_data(self):
        """Test scoring when no token data is present."""
        scorer = TokenUsageScorer()
        
        enriched_output = json.dumps({
            "final_yaml": "test",
            "metrics": {}
        })
        
        score = scorer.score(enriched_output, None, {})
        
        assert score.value == 0.0
        assert "No token usage data" in score.comment
    
    def test_extract_tokens_from_metrics(self):
        """Test extracting token info from metrics."""
        scorer = TokenUsageScorer()
        
        enriched_output = json.dumps({
            "metrics": {
                "total_tokens": 500,
                "prompt_tokens": 100,
                "completion_tokens": 400
            }
        })
        
        token_info = scorer._extract_tokens(enriched_output)
        
        assert token_info["total_tokens"] == 500
        assert token_info["prompt_tokens"] == 100
        assert token_info["completion_tokens"] == 400
