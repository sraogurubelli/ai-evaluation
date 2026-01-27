"""Evaluation agent as unified orchestrator for end-to-end evaluation."""

from typing import Any

from ai_evolution.agents.base import BaseEvaluationAgent
from ai_evolution.agents.experiment_agent import ExperimentAgent
from ai_evolution.agents.task_agent import TaskAgent
from ai_evolution.core.types import ExperimentRun
from ai_evolution.tasks.models import Task, TaskResult


class EvaluationAgent(BaseEvaluationAgent):
    """
    High-level evaluation orchestrator (similar to unified_agent in ml-infra).
    
    Coordinates all other agents for end-to-end evaluation workflows.
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize evaluation agent."""
        super().__init__(config)
        self.experiment_agent = ExperimentAgent(config)
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
        experiment_name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        adapter_config: dict[str, Any],
        model: str | None = None,
        concurrency_limit: int = 5,
        run_async: bool = False,
        **kwargs: Any,
    ) -> Task | ExperimentRun:
        """
        Run a complete evaluation workflow.
        
        This orchestrates:
        1. Creating an experiment
        2. Running the experiment
        3. Optionally creating a task for async execution
        
        Args:
            experiment_name: Name of the experiment
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            adapter_config: Adapter configuration
            model: Optional model name
            concurrency_limit: Concurrency limit for parallel execution
            run_async: If True, create a task for async execution
            **kwargs: Additional parameters
            
        Returns:
            Task (if run_async=True) or ExperimentRun (if run_async=False)
        """
        self.logger.info(f"Starting evaluation: {experiment_name}")
        
        if run_async:
            # Create task for async execution
            config = {
                "dataset": dataset_config,
                "scorers": scorers_config,
                "adapter": adapter_config,
                "execution": {
                    "concurrency_limit": concurrency_limit,
                },
                "models": [model] if model else [None],
            }
            
            task = await self.task_agent.create_task(
                experiment_name=experiment_name,
                config=config,
            )
            
            self.logger.info(f"Created task for async execution: {task.id}")
            return task
        
        else:
            # Run synchronously
            # Create experiment
            experiment = await self.experiment_agent.create_experiment(
                name=experiment_name,
                dataset_config=dataset_config,
                scorers_config=scorers_config,
            )
            
            # Run experiment
            run = await self.experiment_agent.run_experiment(
                experiment=experiment,
                adapter_config=adapter_config,
                model=model,
                concurrency_limit=concurrency_limit,
                **kwargs,
            )
            
            self.logger.info(f"Evaluation completed: {run.run_id}")
            return run
    
    async def stream_evaluation(
        self,
        experiment_name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        adapter_config: dict[str, Any],
        model: str | None = None,
        concurrency_limit: int = 5,
        **kwargs: Any,
    ) -> Any:
        """
        Stream evaluation progress (placeholder for future implementation).
        
        This would yield progress updates as the evaluation runs.
        
        Args:
            experiment_name: Name of the experiment
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            adapter_config: Adapter configuration
            model: Optional model name
            concurrency_limit: Concurrency limit for parallel execution
            **kwargs: Additional parameters
            
        Yields:
            Progress updates
        """
        # Placeholder - would implement streaming logic here
        # For now, just run normally and return result
        self.logger.info(f"Streaming evaluation: {experiment_name}")
        
        result = await self.evaluate(
            experiment_name=experiment_name,
            dataset_config=dataset_config,
            scorers_config=scorers_config,
            adapter_config=adapter_config,
            model=model,
            concurrency_limit=concurrency_limit,
            run_async=False,
            **kwargs,
        )
        
        return result
