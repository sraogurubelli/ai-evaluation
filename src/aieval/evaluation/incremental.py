"""Incremental evaluation for step-level and tool-call-level evaluation."""

from typing import Any
import structlog

from aieval.core.types import Score, EvalResult
from aieval.scorers.base import Scorer

logger = structlog.get_logger(__name__)


class IncrementalEvaluator:
    """
    Evaluator for incremental evaluation (step-level, tool-call-level, parameter-level).
    
    Evaluates individual agent steps, tool calls, and parameters separately.
    """
    
    def __init__(self):
        """Initialize incremental evaluator."""
        self.logger = structlog.get_logger(__name__)
    
    def evaluate_step(
        self,
        step: dict[str, Any],
        expected_step: dict[str, Any] | None = None,
        scorers: list[Scorer] | None = None,
    ) -> list[Score]:
        """
        Evaluate a single agent step.
        
        Args:
            step: Step dictionary with action, parameters, result, etc.
            expected_step: Optional expected step for comparison
            scorers: List of scorers to apply
            
        Returns:
            List of scores for this step
        """
        scores = []
        
        if scorers:
            # Score step result
            step_result = step.get("result") or step.get("output")
            expected_result = expected_step.get("result") if expected_step else None
            
            for scorer in scorers:
                try:
                    score = scorer.score(
                        generated=step_result,
                        expected=expected_result,
                        metadata={
                            "step": step.get("step_number"),
                            "action": step.get("action"),
                            **step.get("metadata", {}),
                        },
                    )
                    scores.append(score)
                except Exception as e:
                    self.logger.error("Error scoring step", step=step.get("step_number"), error=str(e))
        
        return scores
    
    def evaluate_tool_call(
        self,
        tool_call: dict[str, Any],
        expected_tool_call: dict[str, Any] | None = None,
        scorers: list[Scorer] | None = None,
    ) -> list[Score]:
        """
        Evaluate a single tool call.
        
        Args:
            tool_call: Tool call dictionary with tool_name, parameters, result
            expected_tool_call: Optional expected tool call
            scorers: List of scorers to apply
            
        Returns:
            List of scores for this tool call
        """
        scores = []
        
        # Tool call accuracy scorer
        from aieval.scorers.agent import ToolCallAccuracyScorer
        accuracy_scorer = ToolCallAccuracyScorer()
        accuracy_score = accuracy_scorer.score(
            generated=tool_call,
            expected=expected_tool_call,
            metadata={"tool_call_id": tool_call.get("id")},
        )
        scores.append(accuracy_score)
        
        # Parameter correctness scorer
        if expected_tool_call:
            from aieval.scorers.agent import ParameterCorrectnessScorer
            param_scorer = ParameterCorrectnessScorer()
            param_score = param_scorer.score(
                generated=tool_call.get("parameters", {}),
                expected=expected_tool_call.get("parameters", {}),
                metadata={"tool_call_id": tool_call.get("id")},
            )
            scores.append(param_score)
        
        # Score tool result if scorers provided
        if scorers:
            tool_result = tool_call.get("result")
            expected_result = expected_tool_call.get("result") if expected_tool_call else None
            
            for scorer in scorers:
                try:
                    score = scorer.score(
                        generated=tool_result,
                        expected=expected_result,
                        metadata={
                            "tool_name": tool_call.get("tool_name"),
                            "tool_call_id": tool_call.get("id"),
                        },
                    )
                    scores.append(score)
                except Exception as e:
                    self.logger.error("Error scoring tool result", tool=tool_call.get("tool_name"), error=str(e))
        
        return scores
    
    def evaluate_agent_trace(
        self,
        trace: dict[str, Any],
        expected_trace: dict[str, Any] | None = None,
        scorers: list[Scorer] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate an entire agent trace incrementally.
        
        Args:
            trace: Agent trace with steps and tool calls
            expected_trace: Optional expected trace
            scorers: List of scorers to apply
            
        Returns:
            Dictionary with step-level and tool-call-level scores
        """
        results = {
            "step_scores": [],
            "tool_call_scores": [],
            "summary": {},
        }
        
        # Extract steps and tool calls
        steps = trace.get("steps", [])
        expected_steps = expected_trace.get("steps", []) if expected_trace else []
        
        # Evaluate each step
        for i, step in enumerate(steps):
            expected_step = expected_steps[i] if i < len(expected_steps) else None
            step_scores = self.evaluate_step(step, expected_step, scorers)
            results["step_scores"].append({
                "step_number": i + 1,
                "step": step,
                "scores": [s.to_dict() for s in step_scores],
            })
        
        # Extract and evaluate tool calls
        tool_calls = trace.get("tool_calls", [])
        expected_tool_calls = expected_trace.get("tool_calls", []) if expected_trace else []
        
        for i, tool_call in enumerate(tool_calls):
            expected_tool_call = expected_tool_calls[i] if i < len(expected_tool_calls) else None
            tool_scores = self.evaluate_tool_call(tool_call, expected_tool_call, scorers)
            results["tool_call_scores"].append({
                "tool_call_number": i + 1,
                "tool_call": tool_call,
                "scores": [s.to_dict() for s in tool_scores],
            })
        
        # Generate summary
        all_step_scores = []
        for step_result in results["step_scores"]:
            all_step_scores.extend(step_result["scores"])
        
        all_tool_scores = []
        for tool_result in results["tool_call_scores"]:
            all_tool_scores.extend(tool_result["scores"])
        
        results["summary"] = {
            "total_steps": len(steps),
            "total_tool_calls": len(tool_calls),
            "step_scores_count": len(all_step_scores),
            "tool_call_scores_count": len(all_tool_scores),
        }
        
        return results
