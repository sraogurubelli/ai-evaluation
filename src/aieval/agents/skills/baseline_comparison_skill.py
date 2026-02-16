"""Baseline comparison skill."""

from typing import Any

from aieval.agents.skills.base import Skill
from aieval.agents.tools import execute_tool, get_baseline_manager


class BaselineComparisonSkill(Skill):
    """Skill for comparing a run against its baseline."""
    
    def __init__(self):
        super().__init__(
            name="baseline_comparison",
            description="Compare a run against its baseline and detect regressions",
        )
    
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute baseline comparison.
        
        Args:
            eval_id: Evaluation ID
            eval_result: EvalResult to compare (EvalResult object or run_id)
            baseline_eval_result: Optional baseline eval result (if not provided, fetched from baseline manager)
            
        Returns:
            Comparison result with regressions and improvements
        """
        eval_id = kwargs["eval_id"]
        eval_result = kwargs.get("eval_result", kwargs.get("run"))  # Support both names for transition
        
        # Get baseline if not provided
        baseline_eval_result = kwargs.get("baseline_eval_result", kwargs.get("baseline_run"))
        if baseline_eval_result is None:
            baseline_manager = get_baseline_manager()
            baseline_run_id = baseline_manager.get_baseline(eval_id)
            if baseline_run_id is None:
                raise ValueError(f"No baseline set for eval_id: {eval_id}")
            # Note: This requires eval result storage to load the baseline eval result
            # For now, raise an error
            raise NotImplementedError("Baseline comparison requires eval result storage")
        
        # Compare eval results
        result = await execute_tool(
            "compare_eval_results",
            eval_result1=baseline_eval_result,
            eval_result2=eval_result,
        )
        
        if not result.success:
            raise RuntimeError(f"Comparison failed: {result.error}")
        
        return result.data
