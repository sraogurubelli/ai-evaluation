"""Evaluation agent as unified orchestrator for end-to-end evaluation."""

from typing import Any

from aieval.agents.base import BaseEvaluationAgent
from aieval.agents.eval_agent import EvalAgent
from aieval.agents.task_agent import TaskAgent
from aieval.core.types import EvalResult
from aieval.tasks.models import Task, TaskResult


class EvaluationAgent(BaseEvaluationAgent):
    """
    High-level evaluation orchestrator (similar to unified_agent in ml-infra).

    Coordinates all other agents for end-to-end evaluation workflows.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize evaluation agent."""
        super().__init__(config)
        self.eval_agent = EvalAgent(config)
        self.task_agent = TaskAgent(config)

    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run evaluation operation based on query.

        Supported queries:
        - "evaluate": Run a complete evaluation
        - "stream": Stream evaluation progress

        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            Operation result
        """
        if query == "evaluate":
            return await self.evaluate(**kwargs)
        elif query == "stream":
            return await self.stream_evaluation(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")

    async def evaluate(
        self,
        eval_name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        adapter_config: dict[str, Any],
        model: str | None = None,
        models: list[str] | None = None,
        concurrency_limit: int = 5,
        run_async: bool = False,
        agent_id: str | None = None,
        agent_name: str | None = None,
        agent_version: str | None = None,
        **kwargs: Any,
    ) -> Task | EvalResult | list[EvalResult]:
        """
        Run a complete evaluation workflow.

        This orchestrates:
        1. Creating an eval
        2. Running the eval for each model (if multiple models provided)
        3. Optionally creating a task for async execution

        Args:
            eval_name: Name of the eval
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations (metrics/scorers)
            adapter_config: Adapter configuration
            model: [Deprecated] Optional single model name (use 'models' instead)
            models: Optional list of model names to evaluate
            concurrency_limit: Concurrency limit for parallel execution
            run_async: If True, create a task for async execution
            **kwargs: Additional parameters

        Returns:
            Task (if run_async=True) or EvalResult/list[EvalResult] (if run_async=False)
        """
        self.logger.info(f"Starting evaluation: {eval_name}")

        # Normalize models input - prioritize models over model for backward compatibility
        if models:
            model_list = models
        elif model:
            model_list = [model]  # Backward compatibility
        else:
            model_list = [None]  # Use adapter default

        if run_async:
            # Create task for async execution
            config: dict[str, Any] = {
                "dataset": dataset_config,
                "scorers": scorers_config,
                "adapter": adapter_config,
                "execution": {
                    "concurrency_limit": concurrency_limit,
                },
                "models": model_list,
            }
            if agent_id is not None:
                config["agent_id"] = agent_id
            if agent_name is not None:
                config["agent_name"] = agent_name
            if agent_version is not None:
                config["agent_version"] = agent_version

            task = await self.task_agent.create_task(
                eval_name=eval_name,
                config=config,
            )

            self.logger.info(f"Created task for async execution: {task.id}")
            return task

        else:
            # Run synchronously
            # Create eval (shared across all model runs)
            eval_ = await self.eval_agent.create_eval(
                name=eval_name,
                dataset_config=dataset_config,
                scorers_config=scorers_config,
            )

            # Run eval for each model
            run_kwargs = dict(kwargs)
            if agent_id is not None:
                run_kwargs["agent_id"] = agent_id
            if agent_name is not None:
                run_kwargs["agent_name"] = agent_name
            if agent_version is not None:
                run_kwargs["agent_version"] = agent_version
            runs = []
            for model_name in model_list:
                self.logger.info(f"Running eval with model: {model_name or 'default'}")
                run = await self.eval_agent.run_eval(
                    eval_=eval_,
                    adapter_config=adapter_config,
                    model=model_name,
                    concurrency_limit=concurrency_limit,
                    **run_kwargs,
                )
                runs.append(run)
                self.logger.info(f"Completed run {run.run_id} for model: {model_name or 'default'}")

            # Return single run if only one model, list if multiple
            if len(runs) == 1:
                self.logger.info(f"Evaluation completed: {runs[0].run_id}")
                return runs[0]
            else:
                self.logger.info(
                    f"Evaluation completed: {len(runs)} runs for {len(model_list)} models"
                )
                return runs

    async def stream_evaluation(
        self,
        eval_name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        adapter_config: dict[str, Any],
        model: str | None = None,
        models: list[str] | None = None,
        concurrency_limit: int = 5,
        **kwargs: Any,
    ) -> Any:
        """
        Stream evaluation progress (placeholder for future implementation).

        This would yield progress updates as the evaluation runs.

        Args:
            eval_name: Name of the eval
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            adapter_config: Adapter configuration
            model: Optional model name
            models: Optional list of model names
            concurrency_limit: Concurrency limit for parallel execution
            **kwargs: Additional parameters

        Yields:
            Progress updates
        """
        # Placeholder - would implement streaming logic here
        # For now, just run normally and return result
        self.logger.info(f"Streaming evaluation: {eval_name}")

        result = await self.evaluate(
            eval_name=eval_name,
            dataset_config=dataset_config,
            scorers_config=scorers_config,
            adapter_config=adapter_config,
            model=model,
            models=models,
            concurrency_limit=concurrency_limit,
            run_async=False,
            **kwargs,
        )

        return result
