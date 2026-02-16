"""Temporal workflows for AI Evolution Platform.

Workflows orchestrate activities and manage workflow state.
They are deterministic and can be replayed.
"""

import logging
from typing import Any
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy as TemporalRetryPolicy

from aieval.workflows.activities import (
    load_dataset_activity,
    run_eval_activity,
    emit_results_activity,
)

logger = logging.getLogger(__name__)

# Retry policy for workflows
WORKFLOW_RETRY_POLICY = TemporalRetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=3,
)


@workflow.defn(name="eval_workflow")
class EvalWorkflow:
    """
    Workflow for running a single eval.

    This workflow orchestrates:
    1. Loading the dataset
    2. Running the eval
    3. Emitting results to sinks
    """

    @workflow.run
    async def run(
        self,
        eval_name: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run eval workflow.

        Args:
            eval_name: Name of the eval
            config: Eval configuration

        Returns:
            EvalResult as dictionary
        """
        workflow.logger.info(f"Starting eval workflow: {eval_name}")

        # Step 1: Load dataset
        dataset_config = config.get("dataset", {})
        dataset_items = await workflow.execute_activity(
            load_dataset_activity,
            dataset_config,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=TemporalRetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
            ),
        )

        workflow.logger.info(f"Loaded {len(dataset_items)} dataset items")

        # Step 2: Run eval
        execution_config = config.get("execution", {})
        models = config.get("models", [None])
        model = models[0] if models else None

        result = await workflow.execute_activity(
            run_eval_activity,
            args=[
                dataset_items,
                config.get("scorers", []),
                config.get("adapter", {}),
                model,
                execution_config.get("concurrency_limit", 5),
            ],
            start_to_close_timeout=timedelta(hours=2),  # Long timeout for large evals
            retry_policy=TemporalRetryPolicy(
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=3,
            ),
        )

        workflow.logger.info(f"Eval completed: {result.get('run_id')}")

        # Step 3: Emit results (optional, don't fail workflow if this fails)
        sinks_config = config.get("sinks", [])
        if sinks_config:
            try:
                await workflow.execute_activity(
                    emit_results_activity,
                    args=[result, sinks_config],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=TemporalRetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_attempts=2,
                    ),
                )
            except Exception as e:
                workflow.logger.warning(f"Failed to emit results: {e}")
                # Don't fail the workflow if emitting fails

        return result


@workflow.defn(name="multi_model_workflow")
class MultiModelWorkflow:
    """
    Workflow for running evals across multiple models.

    This workflow runs the same eval with different models
    and collects all results.
    """

    @workflow.run
    async def run(
        self,
        eval_name: str,
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Run eval workflow for multiple models.

        Args:
            eval_name: Name of the eval
            config: Eval configuration

        Returns:
            List of EvalResult dictionaries (one per model)
        """
        workflow.logger.info(f"Starting multi-model workflow: {eval_name}")

        models = config.get("models", [None])
        if not models:
            models = [None]

        results = []

        # Run eval for each model sequentially
        # (Could be parallelized with workflow.execute_activity for each)
        for model in models:
            workflow.logger.info(f"Running eval with model: {model or 'default'}")

            # Create single-model config
            single_model_config = config.copy()
            single_model_config["models"] = [model]

            # Run eval workflow as child workflow
            child_result = await workflow.execute_child_workflow(
                EvalWorkflow.run,
                args=[eval_name, single_model_config],
                id=f"{eval_name}-{model or 'default'}",
            )

            results.append(child_result)

        workflow.logger.info(f"Completed {len(results)} model evals")
        return results
