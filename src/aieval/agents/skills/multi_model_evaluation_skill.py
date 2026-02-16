"""Multi-model evaluation skill."""

from typing import Any

from aieval.agents.skills.base import Skill
from aieval.agents.tools import run_tool


class MultiModelEvaluationSkill(Skill):
    """Skill for evaluating multiple models in parallel."""

    def __init__(self):
        super().__init__(
            name="multi_model_evaluation",
            description="Run evaluation across multiple models and compare results",
        )

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute multi-model evaluation.

        Args:
            eval_name: Eval name
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            adapter_config: Adapter configuration
            models: List of model names
            concurrency_limit: Concurrency limit per model (default: 5)

        Returns:
            Dictionary with runs per model and comparison results
        """
        models = kwargs["models"]
        if not models:
            raise ValueError("At least one model must be specified")

        # Run evaluation for each model
        runs = {}
        for model in models:
            result = await run_tool(
                "run_eval",
                eval_name=kwargs["eval_name"],
                dataset_config=kwargs["dataset_config"],
                scorers_config=kwargs["scorers_config"],
                adapter_config=kwargs["adapter_config"],
                model=model,
                concurrency_limit=kwargs.get("concurrency_limit", 5),
            )

            if not result.success:
                runs[model] = {"error": result.error}
            else:
                runs[model] = result.data

        # Compare runs if multiple successful runs
        successful_runs = {k: v for k, v in runs.items() if "error" not in v}
        comparison = None
        if len(successful_runs) > 1:
            # Compare first two successful runs
            run_ids = list(successful_runs.keys())
            compare_result = await run_tool(
                "compare_runs",
                run1=successful_runs[run_ids[0]]["run"],
                run2=successful_runs[run_ids[1]]["run"],
            )
            if compare_result.success:
                comparison = compare_result.data

        return {
            "runs": runs,
            "comparison": comparison,
        }
