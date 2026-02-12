"""Eval core - manages evals and runs."""

import uuid
import asyncio
from typing import Any

from aieval.core.types import DatasetItem, Run, Score, normalize_adapter_output
from aieval.adapters.base import Adapter
from aieval.scorers.base import Scorer


class Eval:
    """Eval container for dataset, scorers, and runs."""

    def __init__(
        self,
        name: str,
        dataset: list[DatasetItem],
        scorers: list[Scorer],
        eval_id: str | None = None,
    ):
        """
        Initialize eval.

        Args:
            name: Eval name
            dataset: List of dataset items
            scorers: List of scorers to apply
            eval_id: Optional eval ID (generated if not provided)
        """
        self.name = name
        self.dataset = dataset
        self.scorers = scorers
        self.eval_id = eval_id or str(uuid.uuid4())
        self.runs: list[Run] = []

    async def run(
        self,
        adapter: Adapter,
        model: str | None = None,
        concurrency_limit: int = 5,
        **kwargs: Any,
    ) -> Run:
        """
        Run eval against dataset.

        Args:
            adapter: Adapter for generating outputs
            model: Model name (optional)
            concurrency_limit: Maximum concurrent API calls
            **kwargs: Additional parameters for adapter

        Returns:
            Run with scores
        """
        run_id = str(uuid.uuid4())
        all_scores: list[Score] = []

        # Generate outputs concurrently
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_item(item: DatasetItem) -> list[Score]:
            """Process a single dataset item."""
            async with semaphore:
                # Generate output
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Processing item {item.id} with {type(adapter).__name__}")
                    output = await adapter.generate(
                        item.input,
                        model=model,
                        **kwargs,
                    )
                    logger.info(f"Output generated for item {item.id}")
                    item.output = output
                except Exception as e:
                    # Create error score
                    return [
                        Score(
                            name="generation_error",
                            value=False,
                            eval_id="generation_error.v1",
                            comment=str(e),
                            metadata={"test_id": item.id, "error": str(e)},
                        )
                    ]

                # Score with all scorers
                item_scores = []
                for scorer in self.scorers:
                    try:
                        score = scorer.score(
                            generated=output,
                            expected=item.expected,
                            metadata={
                                "test_id": item.id,
                                "entity_type": item.input.get("entity_type"),
                                "operation_type": item.input.get("operation_type"),
                                **item.metadata,
                            },
                        )
                        if item.metadata.get("trace_id") and not score.trace_id:
                            score.trace_id = item.metadata["trace_id"]
                        if item.metadata.get("observation_id") and not score.observation_id:
                            score.observation_id = item.metadata["observation_id"]
                        item_scores.append(score)
                    except Exception as e:
                        # Create error score for this scorer
                        item_scores.append(
                            Score(
                                name=scorer.name,
                                value=0.0,
                                eval_id=scorer.eval_id,
                                comment=f"Scorer error: {str(e)}",
                                metadata={"test_id": item.id, "error": str(e)},
                            )
                        )

                return item_scores

        # Process all items
        tasks = [process_item(item) for item in self.dataset]
        results = await asyncio.gather(*tasks)

        # Flatten scores
        for item_scores in results:
            all_scores.extend(item_scores)

        # Create run (agent_id is the unique key for grouping; optional agent_name/agent_version for display)
        run_metadata: dict[str, Any] = {
            "name": self.name,
            "model": model,
            "concurrency_limit": concurrency_limit,
            "dataset_size": len(self.dataset),
            "scorers": [s.name for s in self.scorers],
        }
        for key in ("agent_id", "agent_name", "agent_version"):
            if key in kwargs:
                run_metadata[key] = kwargs.pop(key)
        run = Run(
            eval_id=self.eval_id,
            run_id=run_id,
            dataset_id=str(uuid.uuid4()),  # Could be dataset hash
            scores=all_scores,
            metadata=run_metadata,
        )

        self.runs.append(run)
        return run

    def compare(
        self, run1: Run, run2: Run
    ) -> dict[str, Any]:
        """
        Compare two runs.

        Args:
            run1: First run
            run2: Second run

        Returns:
            Comparison results
        """
        # Group scores by name
        scores1 = {score.name: score.value for score in run1.scores}
        scores2 = {score.name: score.value for score in run2.scores}

        comparison = {
            "run1_id": run1.run_id,
            "run2_id": run2.run_id,
            "score_changes": {},
            "improvements": [],
            "regressions": [],
        }

        # Compare scores
        all_score_names = set(scores1.keys()) | set(scores2.keys())
        for score_name in all_score_names:
            val1 = scores1.get(score_name, 0.0)
            val2 = scores2.get(score_name, 0.0)

            if isinstance(val1, bool):
                val1 = float(val1)
            if isinstance(val2, bool):
                val2 = float(val2)

            change = val2 - val1
            comparison["score_changes"][score_name] = {
                "run1": val1,
                "run2": val2,
                "change": change,
            }

            if change > 0.01:  # Threshold for improvement
                comparison["improvements"].append(score_name)
            elif change < -0.01:  # Threshold for regression
                comparison["regressions"].append(score_name)

        return comparison
