"""Metric scorers for performance analysis.

These scorers analyze performance metrics from enriched adapter output,
such as latency, token usage, and tool calls.
"""

import json
import logging
from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score

logger = logging.getLogger(__name__)


class LatencyScorer(Scorer):
    """
    Scorer that evaluates response latency.
    
    Scores based on whether latency is within acceptable threshold.
    Score is 1.0 if within threshold, decreasing linearly to 0.0 as latency increases.
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
        """Extract latency from generated output."""
        try:
            if isinstance(generated, str):
                # Try to parse as enriched JSON
                data = json.loads(generated)
                if isinstance(data, dict):
                    # Extract from enriched format
                    metrics = data.get("metrics", {})
                    return metrics.get("latency_ms")
            elif isinstance(generated, dict):
                # Direct dict access
                metrics = generated.get("metrics", {})
                return metrics.get("latency_ms")
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
        Score latency performance.
        
        Args:
            generated: Generated output (enriched JSON with metrics)
            expected: Expected output (not used)
            metadata: Additional metadata
            
        Returns:
            Score object with latency evaluation
        """
        latency = self._extract_latency(generated)
        
        if latency is None:
            # Try metadata as fallback
            latency = metadata.get("latency_ms")
        
        if latency is None:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No latency data available",
                metadata=metadata,
            )
        
        # Score: 1.0 if within threshold, decreasing linearly
        if latency <= self.max_latency_ms:
            score_value = 1.0
        else:
            # Linear decrease beyond threshold (0.0 at 2x threshold)
            excess = latency - self.max_latency_ms
            score_value = max(0.0, 1.0 - (excess / self.max_latency_ms))
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=f"Latency: {latency}ms (threshold: {self.max_latency_ms}ms)",
            metadata={
                **metadata,
                "latency_ms": latency,
                "threshold_ms": self.max_latency_ms,
            },
        )


class ToolCallScorer(Scorer):
    """
    Scorer that evaluates tool call usage.
    
    Scores based on whether tools were called (if required) or tracks tool usage.
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
            require_tools: If True, score is 0.0 if no tools called
        """
        super().__init__(name=name, eval_id=eval_id)
        self.require_tools = require_tools
    
    def _extract_tools(self, generated: Any) -> list[dict[str, Any]]:
        """Extract tool calls from generated output."""
        try:
            if isinstance(generated, str):
                # Try to parse as enriched JSON
                data = json.loads(generated)
                if isinstance(data, dict):
                    # Extract from enriched format
                    # Return all events where event == 'assistant_tool_request'
                    events = data.get("events", [])
                    if isinstance(events, list):
                        result = []
                        for event in events:
                            if isinstance(event, dict) and event.get("event") == "assistant_tool_request":
                                result.append(event)
                        return result
                    # Fallback to tools_called for backward compatibility
                    return data.get("tools_called", [])
            elif isinstance(generated, dict):
                # Direct dict access
                # Return all events where event == 'assistant_tool_request'
                # Note: List preserves all elements even if they have the same "event" value
                events = generated.get("events", [])
                if isinstance(events, list):
                    result = []
                    for event in events:
                        if isinstance(event, dict) and event.get("event") == "assistant_tool_request":
                            result.append(event)
                    return result
                # Fallback to tools_called for backward compatibility
                return generated.get("tools_called", [])
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
        Score tool call usage.
        
        Args:
            generated: Generated output (enriched JSON with tools_called)
            expected: Expected output (not used)
            metadata: Additional metadata
            
        Returns:
            Score object with tool call evaluation
        """
        tools = self._extract_tools(generated)
        
        # Fallback to metadata
        if not tools and "tools_called" in metadata:
            tools = metadata.get("tools_called", [])
        
        tool_count = len(tools)
        tools_used = tool_count > 0
        
        # Score logic
        if self.require_tools:
            score_value = 1.0 if tools_used else 0.0
        else:
            # Always 1.0 if not requiring tools (just tracking)
            score_value = 1.0
        
        tool_names = [t.get("tool", "unknown") for t in tools if isinstance(t, dict)]
        comment = f"Tools called: {tool_names}" if tool_names else "No tools called"
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=comment,
            metadata={
                **metadata,
                "tool_count": tool_count,
                "tools_used": tools_used,
                "tools_called": tools,
            },
        )


class TokenUsageScorer(Scorer):
    """
    Scorer that evaluates token usage.
    
    Scores based on whether token usage is within acceptable budget.
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
    
    def _extract_tokens(self, generated: Any) -> dict[str, int] | None:
        """Extract token usage from generated output."""
        try:
            if isinstance(generated, str):
                # Try to parse as enriched JSON
                data = json.loads(generated)
                if isinstance(data, dict):
                    # Extract from enriched format
                    metrics = data.get("metrics", {})
                    if "total_tokens" in metrics:
                        return {
                            "total_tokens": metrics.get("total_tokens", 0),
                            "prompt_tokens": metrics.get("prompt_tokens", 0),
                            "completion_tokens": metrics.get("completion_tokens", 0),
                        }
            elif isinstance(generated, dict):
                # Direct dict access
                metrics = generated.get("metrics", {})
                if "total_tokens" in metrics:
                    return {
                        "total_tokens": metrics.get("total_tokens", 0),
                        "prompt_tokens": metrics.get("prompt_tokens", 0),
                        "completion_tokens": metrics.get("completion_tokens", 0),
                    }
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
        Score token usage.
        
        Args:
            generated: Generated output (enriched JSON with token metrics)
            expected: Expected output (not used)
            metadata: Additional metadata
            
        Returns:
            Score object with token usage evaluation
        """
        token_info = self._extract_tokens(generated)
        
        if token_info is None:
            # Try metadata as fallback
            if "total_tokens" in metadata:
                token_info = {
                    "total_tokens": metadata.get("total_tokens", 0),
                    "prompt_tokens": metadata.get("prompt_tokens", 0),
                    "completion_tokens": metadata.get("completion_tokens", 0),
                }
        
        if token_info is None:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No token usage data available",
                metadata=metadata,
            )
        
        total_tokens = token_info.get("total_tokens", 0)
        
        # Score: 1.0 if within budget, decreasing linearly
        if total_tokens <= self.max_tokens:
            score_value = 1.0
        else:
            # Linear decrease beyond budget (0.0 at 2x budget)
            excess = total_tokens - self.max_tokens
            score_value = max(0.0, 1.0 - (excess / self.max_tokens))
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=f"Token usage: {total_tokens}/{self.max_tokens}",
            metadata={
                **metadata,
                "total_tokens": total_tokens,
                "prompt_tokens": token_info.get("prompt_tokens", 0),
                "completion_tokens": token_info.get("completion_tokens", 0),
                "token_budget": self.max_tokens,
            },
        )

