"""Eval-related tools."""

from typing import Any
import uuid

from aieval.agents.tools.base import Tool, ToolResult
from aieval.core.eval import Eval
from aieval.core.types import DatasetItem, EvalResult
from aieval.scorers.base import Scorer
from aieval.adapters.base import Adapter


class CreateEvalTool(Tool):
    """Tool for creating eval definitions."""

    def __init__(self):
        super().__init__(
            name="create_eval",
            description="Create an eval definition with dataset and scorers",
            parameters_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Eval name",
                    },
                    "eval_id": {
                        "type": "string",
                        "description": "Optional eval ID (generated if not provided)",
                    },
                    "dataset": {
                        "type": "array",
                        "description": "List of dataset items (from load_dataset tool)",
                        "items": {"type": "object"},
                    },
                    "scorers": {
                        "type": "array",
                        "description": "List of scorer configs (from create_scorer tool)",
                        "items": {"type": "object"},
                    },
                },
                "required": ["name", "dataset", "scorers"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute eval creation."""
        try:
            self.validate_parameters(**kwargs)

            # Note: This tool creates an eval definition but doesn't store it
            # The actual Eval object is created when needed
            # This is a placeholder that returns eval metadata

            name = kwargs["name"]
            eval_id = kwargs.get("eval_id") or str(uuid.uuid4())
            dataset = kwargs["dataset"]
            scorers = kwargs["scorers"]

            return ToolResult(
                success=True,
                data={
                    "eval": {
                        "name": name,
                        "eval_id": eval_id,
                        "dataset_count": len(dataset),
                        "scorer_count": len(scorers),
                    },
                },
                metadata={"eval_id": eval_id},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class EvalTool(Tool):
    """Tool for running evaluations."""

    def __init__(self):
        super().__init__(
            name="eval",
            description="Run an evaluation with dataset, scorers, and adapter",
            parameters_schema={
                "type": "object",
                "properties": {
                    "eval_name": {
                        "type": "string",
                        "description": "Eval name",
                    },
                    "dataset_config": {
                        "type": "object",
                        "description": "Dataset configuration (same as load_dataset parameters)",
                    },
                    "scorers_config": {
                        "type": "array",
                        "description": "List of scorer configurations",
                        "items": {"type": "object"},
                    },
                    "adapter_config": {
                        "type": "object",
                        "description": "Adapter configuration",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model name (optional)",
                    },
                    "concurrency_limit": {
                        "type": "integer",
                        "description": "Maximum concurrent API calls",
                        "default": 5,
                    },
                    "eval_id": {
                        "type": "string",
                        "description": "Optional eval ID",
                    },
                },
                "required": ["eval_name", "dataset_config", "scorers_config", "adapter_config"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute evaluation run."""
        try:
            self.validate_parameters(**kwargs)

            # Import here to avoid circular dependencies
            from aieval.agents.tools.dataset_tools import LoadDatasetTool
            from aieval.agents.tools.scorer_tools import CreateScorerTool
            from aieval.cli.main import _create_adapter

            # Load dataset
            load_dataset_tool = LoadDatasetTool()
            dataset_result = await load_dataset_tool.execute(**kwargs["dataset_config"])
            if not dataset_result.success:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Failed to load dataset: {dataset_result.error}",
                )

            dataset_items = [DatasetItem(**item) for item in dataset_result.data["dataset"]]

            # Create scorers using the helper function from CLI
            # Import here to avoid circular dependencies
            from aieval.cli.main import _create_scorers

            scorers = _create_scorers({"scorers": kwargs["scorers_config"]})

            # Create adapter
            adapter = _create_adapter({"adapter": kwargs["adapter_config"]})

            # Create eval
            eval_ = Eval(
                name=kwargs["eval_name"],
                dataset=dataset_items,
                scorers=scorers,
                eval_id=kwargs.get("eval_id"),
            )

            # Run eval
            run = await eval_.run(
                adapter=adapter,
                model=kwargs.get("model"),
                concurrency_limit=kwargs.get("concurrency_limit", 5),
            )

            return ToolResult(
                success=True,
                data={
                    "run": run.to_dict(),
                    "run_id": run.run_id,
                    "eval_id": run.eval_id,
                },
                metadata={"run_id": run.run_id},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
