"""Metric-specific scorers for performance analysis.

These scorers analyze performance metrics from enriched adapter output,
including latency, tool usage, and token consumption.
"""

import json
import logging
from typing import Any

from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score

logger = logging.getLogger(__name__)


class LatencyScorer(Scorer):
    """
    Score based on response latency.
    
    Scores the latency of API responses with configurable thresholds.
    Lower latency receives higher scores.
    
    Example:
        scorer = LatencyScorer(max_latency_ms=30000)
        score = scorer.score(enriched_output, expected, metadata)
    """
    
    def __init__(
        self,
        max_latency_ms: int = 30000,
        name: str = "latency",
        eval_id: str = "latency.v1",
    ):
        """
        Initialize latency scorer.
        
        Args:
            max_latency_ms: Maximum acceptable latency in milliseconds
            name: Score name
            eval_id: Evaluation ID
        """
        super().__init__(name=name, eval_id=eval_id)
        self.max_latency_ms = max_latency_ms
    
    def _extract_latency(self, generated: Any) -> int | None:
        """Extract latency from enriched output."""
        try:
            # Try to parse as enriched JSON
            if isinstance(generated, str):
                data = json.loads(generated)
            else:
                data = generated
            
            # Extract from enriched format
            if isinstance(data, dict):
                # Check in metrics
                if "metrics" in data and isinstance(data["metrics"], dict):
                    return data["metrics"].get("latency_ms")
                # Check at root level
                if "latency_ms" in data:
                    return data["latency_ms"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        return None
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score based on latency.
        
        Args:
            generated: Generated output (enriched JSON with metrics)
            expected: Expected output (unused)
            metadata: Additional metadata
            
        Returns:
            Score with value between 0.0 and 1.0:
            - 1.0 if latency <= max_latency_ms
            - Linear decay to 0.0 as latency increases
        """
        # Extract latency
        latency_ms = self._extract_latency(generated)
        
        if latency_ms is None:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No latency data found in output",
                metadata=metadata,
            )
        
        # Calculate score (1.0 if under threshold, decreasing linearly)
        if latency_ms <= self.max_latency_ms:
            score_value = 1.0
        else:
            # Linear decay: score approaches 0 as latency increases beyond threshold
            score_value = max(0.0, 1.0 - ((latency_ms - self.max_latency_ms) / self.max_latency_ms))
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=f"Latency: {latency_ms}ms (threshold: {self.max_latency_ms}ms)",
            metadata={
                **metadata,
                "latency_ms": latency_ms,
                "threshold_ms": self.max_latency_ms,
            },
        )


class ToolCallScorer(Scorer):
    """
    Analyze tool calls from streaming events.
    
    Scores based on whether tools were called and extracts tool information.
    Useful for validating agent behavior and debugging.
    
    Example:
        scorer = ToolCallScorer()
        score = scorer.score(enriched_output, expected, metadata)
    """
    
    def __init__(
        self,
        name: str = "tool_calls",
        eval_id: str = "tool_calls.v1",
        require_tools: bool = False,
    ):
        """
        Initialize tool call scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            require_tools: If True, score is 1.0 when tools used, 0.0 otherwise
                          If False, just reports tool usage (always 1.0)
        """
        super().__init__(name=name, eval_id=eval_id)
        self.require_tools = require_tools
    
    def _extract_tools(self, generated: Any) -> list[dict[str, Any]]:
        """Extract tool calls from enriched output."""
        try:
            # Try to parse as enriched JSON
            if isinstance(generated, str):
                data = json.loads(generated)
            else:
                data = generated
            
            # Extract from enriched format
            if isinstance(data, dict) and "tools_called" in data:
                return data["tools_called"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        return []
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score based on tool calls.
        
        Args:
            generated: Generated output (enriched JSON with tools_called)
            expected: Expected output (unused)
            metadata: Additional metadata
            
        Returns:
            Score indicating tool usage
        """
        # Extract tools
        tools_called = self._extract_tools(generated)
        tools_used = len(tools_called) > 0
        
        # Calculate score
        if self.require_tools:
            score_value = 1.0 if tools_used else 0.0
        else:
            # Always return 1.0, just report usage
            score_value = 1.0
        
        # Build comment
        if tools_used:
            tool_names = [t.get("tool", "unknown") for t in tools_called]
            comment = f"Tools called: {tool_names}"
        else:
            comment = "No tools called"
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=comment,
            metadata={
                **metadata,
                "tools_called": tools_called,
                "tool_count": len(tools_called),
                "tools_used": tools_used,
            },
        )


class TokenUsageScorer(Scorer):
    """
    Track and score token consumption.
    
    Scores based on token usage efficiency with configurable budgets.
    Lower token usage receives higher scores.
    
    Example:
        scorer = TokenUsageScorer(max_tokens=5000)
        score = scorer.score(enriched_output, expected, metadata)
    """
    
    def __init__(
        self,
        max_tokens: int = 10000,
        name: str = "token_usage",
        eval_id: str = "token_usage.v1",
    ):
        """
        Initialize token usage scorer.
        
        Args:
            max_tokens: Maximum acceptable token count
            name: Score name
            eval_id: Evaluation ID
        """
        super().__init__(name=name, eval_id=eval_id)
        self.max_tokens = max_tokens
    
    def _extract_tokens(self, generated: Any) -> dict[str, int]:
        """Extract token usage from enriched output."""
        token_info = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
        
        try:
            # Try to parse as enriched JSON
            if isinstance(generated, str):
                data = json.loads(generated)
            else:
                data = generated
            
            # Extract from enriched format
            if isinstance(data, dict) and "metrics" in data:
                metrics = data["metrics"]
                if isinstance(metrics, dict):
                    token_info["total_tokens"] = metrics.get("total_tokens", 0)
                    token_info["prompt_tokens"] = metrics.get("prompt_tokens", 0)
                    token_info["completion_tokens"] = metrics.get("completion_tokens", 0)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        return token_info
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score based on token usage.
        
        Args:
            generated: Generated output (enriched JSON with token metrics)
            expected: Expected output (unused)
            metadata: Additional metadata
            
        Returns:
            Score with value between 0.0 and 1.0:
            - 1.0 if tokens <= max_tokens
            - Linear decay to 0.0 as token usage increases
        """
        # Extract token usage
        token_info = self._extract_tokens(generated)
        total_tokens = token_info["total_tokens"]
        
        if total_tokens == 0:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No token usage data found in output",
                metadata=metadata,
            )
        
        # Calculate score (1.0 if under budget, decreasing linearly)
        if total_tokens <= self.max_tokens:
            score_value = 1.0
        else:
            # Linear decay: score approaches 0 as usage increases beyond budget
            score_value = max(0.0, 1.0 - ((total_tokens - self.max_tokens) / self.max_tokens))
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=f"Tokens: {total_tokens} (budget: {self.max_tokens})",
            metadata={
                **metadata,
                "total_tokens": total_tokens,
                "prompt_tokens": token_info["prompt_tokens"],
                "completion_tokens": token_info["completion_tokens"],
                "token_budget": self.max_tokens,
            },
        )
