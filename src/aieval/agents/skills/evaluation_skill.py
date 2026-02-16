"""Evaluation skill - complete evaluation workflow."""

from typing import Any

from aieval.agents.skills.base import Skill
from aieval.agents.tools import run_tool


class EvaluationSkill(Skill):
    """Skill for running a complete evaluation workflow."""
    
    def __init__(self):
        super().__init__(
            name="evaluation",
            description="Run a complete evaluation workflow: load dataset, create scorers, run eval",
        )
    
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute evaluation workflow.
        
        Args:
            eval_name: Eval name
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            adapter_config: Adapter configuration
            model: Optional model name
            concurrency_limit: Concurrency limit (default: 5)
            
        Returns:
            Run result
        """
        # Use RunEvalTool internally
        result = await run_tool(
            "run_eval",
            eval_name=kwargs["eval_name"],
            dataset_config=kwargs["dataset_config"],
            scorers_config=kwargs["scorers_config"],
            adapter_config=kwargs["adapter_config"],
            model=kwargs.get("model"),
            concurrency_limit=kwargs.get("concurrency_limit", 5),
        )
        
        if not result.success:
            raise RuntimeError(f"Evaluation failed: {result.error}")
        
        return result.data
