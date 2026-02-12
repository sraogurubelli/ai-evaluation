"""Eval agent for orchestrating eval execution."""

import uuid
from typing import Any

from aieval.agents.base import BaseEvaluationAgent
from aieval.agents.dataset_agent import DatasetAgent
from aieval.agents.scorer_agent import ScorerAgent
from aieval.agents.adapter_agent import AdapterAgent
from aieval.core.eval import Eval
from aieval.core.types import Run, DatasetItem
from aieval.adapters.base import Adapter
from aieval.scorers.base import Scorer


class EvalAgent(BaseEvaluationAgent):
    """Agent for eval orchestration."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize eval agent."""
        super().__init__(config)
        self.dataset_agent = DatasetAgent(config)
        self.scorer_agent = ScorerAgent(config)
        self.adapter_agent = AdapterAgent(config)
        self._evals: dict[str, Eval] = {}

    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run eval operation based on query.

        Supported queries:
        - "create": Create an eval
        - "run": Run an eval
        - "compare": Compare runs

        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            Operation result
        """
        if query == "create":
            return await self.create_eval(**kwargs)
        elif query == "run":
            return await self.run_eval(**kwargs)
        elif query == "compare":
            return await self.compare_runs(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")

    async def create_eval(
        self,
        name: str,
        dataset_config: dict[str, Any],
        scorers_config: list[dict[str, Any]],
        eval_id: str | None = None,
        **kwargs: Any,
    ) -> Eval:
        """
        Create an eval.

        Args:
            name: Eval name
            dataset_config: Dataset configuration
            scorers_config: List of scorer configurations
            eval_id: Optional eval ID
            **kwargs: Additional parameters

        Returns:
            Created eval instance
        """
        self.logger.info(f"Creating eval: {name}")

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

        # Create eval
        eval_ = Eval(
            name=name,
            dataset=dataset,
            scorers=scorers,
            eval_id=eval_id,
        )

        # Cache eval
        if eval_.eval_id:
            self._evals[eval_.eval_id] = eval_

        self.logger.info(f"Created eval: {name} (ID: {eval_.eval_id})")
        return eval_

    async def run_eval(
        self,
        eval_: Eval | str,
        adapter_config: dict[str, Any],
        model: str | None = None,
        concurrency_limit: int = 5,
        **kwargs: Any,
    ) -> Run:
        """
        Run an eval.

        Args:
            eval_: Eval instance or eval ID
            adapter_config: Adapter configuration
            model: Optional model name
            concurrency_limit: Concurrency limit for parallel execution
            **kwargs: Additional parameters

        Returns:
            Run result
        """
        # Resolve eval if ID provided
        if isinstance(eval_, str):
            if eval_ not in self._evals:
                raise ValueError(f"Eval {eval_} not found. Create it first.")
            eval_ = self._evals[eval_]

        # Create adapter
        adapter_type = adapter_config.get("type", "http")
        adapter = await self.adapter_agent.create_adapter(
            adapter_type=adapter_type,
            **{k: v for k, v in adapter_config.items() if k != "type"},
        )

        self.logger.info(f"Running eval: {eval_.name}")

        # Run eval
        run = await eval_.run(
            adapter=adapter,
            model=model,
            concurrency_limit=concurrency_limit,
            **kwargs,
        )

        self.logger.info(f"Eval run completed: {run.run_id}")
        return run

    async def compare_runs(
        self,
        run1: Run | str,
        run2: Run | str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Compare two runs.

        Args:
            run1: First run or run ID
            run2: Second run or run ID
            **kwargs: Additional parameters

        Returns:
            Comparison result
        """
        self.logger.info("Comparing runs")

        return {
            "run1_id": run1.run_id if isinstance(run1, Run) else run1,
            "run2_id": run2.run_id if isinstance(run2, Run) else run2,
            "comparison": "Not implemented yet",
        }
