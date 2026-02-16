"""Online evaluation tools."""

from typing import Any

from aieval.agents.tools.base import Tool, ToolResult
from aieval.evaluation.online import OnlineEvaluationAgent
from aieval.datasets.trace_converter import traces_to_dataset
from aieval.monitoring.evaluator import ContinuousEvaluator
from aieval.feedback.collector import FeedbackCollector


class EvaluateTraceTool(Tool):
    """Tool for evaluating a single production trace."""

    def __init__(self):
        super().__init__(
            name="evaluate_trace",
            description="Evaluate a single production trace",
            parameters_schema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "Trace ID from tracing system",
                    },
                    "trace_source": {
                        "type": "string",
                        "enum": ["langfuse", "otel"],
                        "description": "Trace source",
                        "default": "langfuse",
                    },
                    "scorers_config": {
                        "type": "array",
                        "description": "List of scorer configurations",
                        "items": {"type": "object"},
                    },
                },
                "required": ["trace_id", "scorers_config"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute trace evaluation."""
        try:
            self.validate_parameters(**kwargs)

            # Import here to avoid circular dependencies
            from aieval.cli.main import _create_scorers

            # Create scorers
            scorers = _create_scorers({"scorers": kwargs["scorers_config"]})

            # Create agent
            agent = OnlineEvaluationAgent()

            # Evaluate trace
            run = await agent.evaluate_trace(
                trace_id=kwargs["trace_id"],
                trace_source=kwargs.get("trace_source", "langfuse"),
                scorers=scorers,
            )

            return ToolResult(
                success=True,
                data={
                    "run": run.to_dict(),
                    "run_id": run.run_id,
                },
                metadata={"trace_id": kwargs["trace_id"]},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class EvaluateTracesTool(Tool):
    """Tool for evaluating multiple production traces."""

    def __init__(self):
        super().__init__(
            name="evaluate_traces",
            description="Evaluate multiple production traces",
            parameters_schema={
                "type": "object",
                "properties": {
                    "trace_ids": {
                        "type": "array",
                        "description": "List of trace IDs",
                        "items": {"type": "string"},
                    },
                    "trace_source": {
                        "type": "string",
                        "enum": ["langfuse", "otel"],
                        "description": "Trace source",
                        "default": "langfuse",
                    },
                    "scorers_config": {
                        "type": "array",
                        "description": "List of scorer configurations",
                        "items": {"type": "object"},
                    },
                },
                "required": ["trace_ids", "scorers_config"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute traces evaluation."""
        try:
            self.validate_parameters(**kwargs)

            from aieval.cli.main import _create_scorers

            # Create scorers
            scorers = _create_scorers({"scorers": kwargs["scorers_config"]})

            # Create evaluator
            evaluator = ContinuousEvaluator(
                trace_source=kwargs.get("trace_source", "langfuse"),
                scorers=scorers,
            )

            # Evaluate traces
            runs = await evaluator.evaluate_traces(trace_ids=kwargs["trace_ids"])

            return ToolResult(
                success=True,
                data={
                    "runs": [run.to_dict() for run in runs],
                    "count": len(runs),
                },
                metadata={"trace_source": kwargs.get("trace_source", "langfuse")},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class ConvertTracesToDatasetTool(Tool):
    """Tool for converting traces to dataset."""

    def __init__(self):
        super().__init__(
            name="convert_traces_to_dataset",
            description="Convert production traces to a dataset",
            parameters_schema={
                "type": "object",
                "properties": {
                    "traces": {
                        "type": "array",
                        "description": "List of trace dictionaries",
                        "items": {"type": "object"},
                    },
                    "trace_source": {
                        "type": "string",
                        "enum": ["langfuse", "otel"],
                        "description": "Trace source",
                        "default": "langfuse",
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters",
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Optional sample size",
                    },
                    "sampling_strategy": {
                        "type": "string",
                        "enum": ["random", "stratified"],
                        "description": "Sampling strategy",
                        "default": "random",
                    },
                },
                "required": ["traces"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute trace conversion."""
        try:
            self.validate_parameters(**kwargs)

            dataset = traces_to_dataset(
                traces=kwargs["traces"],
                trace_source=kwargs.get("trace_source", "langfuse"),
                filters=kwargs.get("filters"),
                sample_size=kwargs.get("sample_size"),
                sampling_strategy=kwargs.get("sampling_strategy", "random"),
            )

            return ToolResult(
                success=True,
                data={
                    "dataset": [item.to_dict() for item in dataset],
                    "count": len(dataset),
                },
                metadata={"trace_source": kwargs.get("trace_source", "langfuse")},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class MonitorTracesTool(Tool):
    """Tool for setting up continuous monitoring."""

    def __init__(self):
        super().__init__(
            name="monitor_traces",
            description="Set up continuous monitoring of traces",
            parameters_schema={
                "type": "object",
                "properties": {
                    "trace_source": {
                        "type": "string",
                        "enum": ["langfuse", "otel"],
                        "description": "Trace source",
                        "default": "langfuse",
                    },
                    "scorers_config": {
                        "type": "array",
                        "description": "List of scorer configurations",
                        "items": {"type": "object"},
                    },
                    "interval_seconds": {
                        "type": "integer",
                        "description": "Polling interval in seconds",
                        "default": 60,
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters",
                    },
                },
                "required": ["scorers_config"],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute monitoring setup."""
        try:
            self.validate_parameters(**kwargs)

            from aieval.cli.main import _create_scorers

            # Create scorers
            scorers = _create_scorers({"scorers": kwargs["scorers_config"]})

            # Create evaluator
            evaluator = ContinuousEvaluator(
                trace_source=kwargs.get("trace_source", "langfuse"),
                scorers=scorers,
            )

            # Start monitoring (this runs in background)
            import asyncio

            monitoring_task = asyncio.create_task(
                evaluator.start_monitoring(
                    interval_seconds=kwargs.get("interval_seconds", 60),
                    filters=kwargs.get("filters"),
                )
            )

            return ToolResult(
                success=True,
                data={
                    "monitoring_started": True,
                    "trace_source": kwargs.get("trace_source", "langfuse"),
                },
                metadata={"interval_seconds": kwargs.get("interval_seconds", 60)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


class CollectFeedbackTool(Tool):
    """Tool for collecting user feedback."""

    def __init__(self):
        super().__init__(
            name="collect_feedback",
            description="Collect user feedback for a trace or run",
            parameters_schema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "Optional trace ID",
                    },
                    "run_id": {
                        "type": "string",
                        "description": "Optional run ID",
                    },
                    "rating": {
                        "type": "integer",
                        "description": "Rating (1-5)",
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "thumbs_up": {
                        "type": "boolean",
                        "description": "Thumbs up/down",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment",
                    },
                },
                "required": [],
            },
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute feedback collection."""
        try:
            self.validate_parameters(**kwargs)

            collector = FeedbackCollector()
            feedback_id = collector.collect_feedback(**kwargs)

            return ToolResult(
                success=True,
                data={
                    "feedback_id": feedback_id,
                },
                metadata=kwargs,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )
