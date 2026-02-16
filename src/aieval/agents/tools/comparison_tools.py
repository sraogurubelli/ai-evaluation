"""Comparison-related tools."""

from typing import Any

from aieval.agents.tools.base import Tool, ToolResult
from aieval.core.types import EvalResult


class CompareEvalResultsTool(Tool):
    """Tool for comparing two eval results."""
    
    def __init__(self):
        super().__init__(
            name="compare_eval_results",
            description="Compare two evaluation results",
            parameters_schema={
                "type": "object",
                "properties": {
                    "eval_result1": {
                        "type": "object",
                        "description": "First eval result (EvalResult object or run_id)",
                    },
                    "eval_result2": {
                        "type": "object",
                        "description": "Second eval result (EvalResult object or run_id)",
                    },
                },
                "required": ["eval_result1", "eval_result2"],
            },
        )
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute eval result comparison."""
        try:
            self.validate_parameters(**kwargs)
            
            eval_result1_data = kwargs["eval_result1"]
            eval_result2_data = kwargs["eval_result2"]
            
            # Convert dict to EvalResult objects if needed
            if isinstance(eval_result1_data, dict):
                from aieval.core.types import Score
                from datetime import datetime
                eval_result1 = EvalResult(
                    eval_id=eval_result1_data["eval_id"],
                    run_id=eval_result1_data["run_id"],
                    dataset_id=eval_result1_data["dataset_id"],
                    scores=[Score(**s) for s in eval_result1_data.get("scores", [])],
                    metadata=eval_result1_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(eval_result1_data["created_at"]) if isinstance(eval_result1_data.get("created_at"), str) else eval_result1_data.get("created_at", datetime.now()),
                )
            else:
                eval_result1 = eval_result1_data
            
            if isinstance(eval_result2_data, dict):
                from aieval.core.types import Score
                from datetime import datetime
                eval_result2 = EvalResult(
                    eval_id=eval_result2_data["eval_id"],
                    run_id=eval_result2_data["run_id"],
                    dataset_id=eval_result2_data["dataset_id"],
                    scores=[Score(**s) for s in eval_result2_data.get("scores", [])],
                    metadata=eval_result2_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(eval_result2_data["created_at"]) if isinstance(eval_result2_data.get("created_at"), str) else eval_result2_data.get("created_at", datetime.now()),
                )
            else:
                eval_result2 = eval_result2_data
            
            # Compare eval results (using Eval.compare method)
            from aieval.core.eval import Eval
            # Create a dummy eval for comparison
            eval_ = Eval(name="comparison", dataset=[], scorers=[])
            comparison = eval_.compare(eval_result1, eval_result2)
            
            return ToolResult(
                success=True,
                data=comparison,
                metadata={
                    "eval_result1_id": eval_result1.run_id,
                    "eval_result2_id": eval_result2.run_id,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
