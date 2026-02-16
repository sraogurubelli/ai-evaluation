"""Tool call accuracy scorer for agent evaluation."""

from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score


class ToolCallAccuracyScorer(Scorer):
    """Scorer for evaluating if agent chose the correct tool."""
    
    def __init__(self, name: str = "tool_call_accuracy", eval_id: str = "tool_call_accuracy.v1"):
        """
        Initialize tool call accuracy scorer.
        
        Args:
            name: Scorer name
            eval_id: Evaluation ID
        """
        super().__init__(name=name, eval_id=eval_id)
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score tool call accuracy.
        
        Args:
            generated: Generated tool call (dict with "tool_name" key)
            expected: Expected tool call (dict with "tool_name" key)
            metadata: Additional metadata
            
        Returns:
            Score object (True if correct tool, False otherwise)
        """
        # Extract tool names
        generated_tool = None
        expected_tool = None
        
        if isinstance(generated, dict):
            generated_tool = generated.get("tool_name") or generated.get("name")
        elif isinstance(generated, str):
            generated_tool = generated
        
        if isinstance(expected, dict):
            expected_tool = expected.get("tool_name") or expected.get("name")
        elif isinstance(expected, str):
            expected_tool = expected
        
        # Compare
        is_correct = generated_tool == expected_tool
        
        return Score(
            name=self.name,
            value=is_correct,
            eval_id=self.eval_id,
            comment=f"Expected: {expected_tool}, Got: {generated_tool}",
            metadata=metadata,
        )
