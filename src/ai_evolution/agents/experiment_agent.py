"""Experiment agent for orchestrating experiment execution."""

import uuid
from typing import Any

from ai_evolution.agents.base import BaseEvaluationAgent
from ai_evolution.agents.dataset_agent import DatasetAgent
from ai_evolution.agents.scorer_agent import ScorerAgent
from ai_evolution.agents.adapter_agent import AdapterAgent
from ai_evolution.core.experiment import Experiment
from ai_evolution.core.types import ExperimentRun, DatasetItem
from ai_evolution.adapters.base import Adapter
from ai_evolution.scorers.base import Scorer


class ExperimentAgent(BaseEvaluationAgent):
    """Agent for experiment orchestration."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize experiment agent."""
        super().__init__(config)
        self.dataset_agent = DatasetAgent(config)
        self.scorer_agent = ScorerAgent(config)
        self.adapter_agent = AdapterAgent(config)
        self._experiments: dict[str, Experiment] = {}
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run experiment operation based on query.
        
        Supported queries:
        - "create": Create an experiment
        - "run": Run an experiment
        - "compare": Compare experiment runs
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "create":
            return await self.create_experiment(**kwargs)
        elif query == "run":
            return await self.run_experiment(**kwargs)
        elif query == "compare":
            return await self.compare_runs(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def create_experiment(
        self,
        name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        experiment_id: str | None = None,
        **kwargs: Any,
    ) -> Experiment:
        """
        Create an experiment.
        
        Args:
            name: Experiment name
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            experiment_id: Optional experiment ID
            **kwargs: Additional parameters
            
        Returns:
            Created experiment instance
        """
        self.logger.info(f"Creating experiment: {name}")
        
        # Load dataset
        dataset_type = dataset_config.get("type", "jsonl")
        dataset = await self.dataset_agent.load_dataset(
            dataset_type=dataset_type,
            **{k: v for k, v in dataset_config.items() if k != "type"},
        )
        
        # Create scorers
        scorers = []
        for scorer_config in scorers_config:
            scorer_type = scorer_config.get("type")
            scorer = await self.scorer_agent.create_scorer(
                scorer_type=scorer_type,
                **{k: v for k, v in scorer_config.items() if k != "type"},
            )
            scorers.append(scorer)
        
        # Create experiment
        experiment = Experiment(
            name=name,
            dataset=dataset,
            scorers=scorers,
            experiment_id=experiment_id,
        )
        
        # Cache experiment
        if experiment.experiment_id:
            self._experiments[experiment.experiment_id] = experiment
        
        self.logger.info(f"Created experiment: {name} (ID: {experiment.experiment_id})")
        return experiment
    
    async def run_experiment(
        self,
        experiment: Experiment | str,
        adapter_config: dict[str, Any],
        model: str | None = None,
        concurrency_limit: int = 5,
        **kwargs: Any,
    ) -> ExperimentRun:
        """
        Run an experiment.
        
        Args:
            experiment: Experiment instance or experiment ID
            adapter_config: Adapter configuration
            model: Optional model name
            concurrency_limit: Concurrency limit for parallel execution
            **kwargs: Additional parameters
            
        Returns:
            Experiment run result
        """
        # Resolve experiment if ID provided
        if isinstance(experiment, str):
            if experiment not in self._experiments:
                raise ValueError(f"Experiment {experiment} not found. Create it first.")
            experiment = self._experiments[experiment]
        
        # Create adapter
        adapter_type = adapter_config.get("type", "http")
        adapter = await self.adapter_agent.create_adapter(
            adapter_type=adapter_type,
            **{k: v for k, v in adapter_config.items() if k != "type"},
        )
        
        self.logger.info(f"Running experiment: {experiment.name}")
        
        # Run experiment
        run = await experiment.run(
            adapter=adapter,
            model=model,
            concurrency_limit=concurrency_limit,
            **kwargs,
        )
        
        self.logger.info(f"Experiment run completed: {run.run_id}")
        return run
    
    async def compare_runs(
        self,
        run1: ExperimentRun | str,
        run2: ExperimentRun | str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Compare two experiment runs.
        
        Args:
            run1: First experiment run or run ID
            run2: Second experiment run or run ID
            **kwargs: Additional parameters
            
        Returns:
            Comparison result
        """
        # For now, this is a placeholder - actual comparison logic would go here
        # The Experiment class has a compare() method that can be used
        
        self.logger.info("Comparing experiment runs")
        
        return {
            "run1_id": run1.run_id if isinstance(run1, ExperimentRun) else run1,
            "run2_id": run2.run_id if isinstance(run2, ExperimentRun) else run2,
            "comparison": "Not implemented yet",
        }
