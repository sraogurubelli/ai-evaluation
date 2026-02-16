"""Continuous evaluator for automatic trace evaluation."""

from typing import Any
import asyncio
import structlog
from datetime import datetime

from aieval.evaluation.online import OnlineEvaluationAgent
from aieval.core.types import EvalResult
from aieval.scorers.base import Scorer

logger = structlog.get_logger(__name__)


class ContinuousEvaluator:
    """
    Continuous evaluator that automatically evaluates traces.
    
    Supports both scheduled evaluation (cron-like) and event-driven evaluation.
    """
    
    def __init__(
        self,
        trace_source: str = "langfuse",
        scorers: list[Scorer] | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize continuous evaluator.
        
        Args:
            trace_source: Trace source ("langfuse", "otel", etc.)
            scorers: List of scorers to apply
            config: Configuration dictionary
        """
        self.trace_source = trace_source
        self.scorers = scorers or []
        self.config = config or {}
        self.agent = OnlineEvaluationAgent(config)
        self.logger = structlog.get_logger(__name__)
        self._running = False
        self._evaluation_results: list[EvalResult] = []
    
    async def evaluate_traces(
        self,
        trace_ids: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[EvalResult]:
        """
        Evaluate multiple traces.
        
        Args:
            trace_ids: Optional list of specific trace IDs to evaluate
            filters: Optional filters for trace selection
            **kwargs: Additional parameters
            
        Returns:
            List of EvalResult objects
        """
        if trace_ids:
            # Evaluate specific traces
            runs = []
            for trace_id in trace_ids:
                try:
                    run = await self.agent.evaluate_trace(
                        trace_id=trace_id,
                        trace_source=self.trace_source,
                        scorers=self.scorers,
                        **kwargs,
                    )
                    runs.append(run)
                    self._evaluation_results.append(run)
                except Exception as e:
                    self.logger.error(
                        "Failed to evaluate trace",
                        trace_id=trace_id,
                        error=str(e),
                    )
            return runs
        else:
            # Fetch traces based on filters and evaluate
            # This would need trace fetching logic
            raise NotImplementedError("Automatic trace fetching not yet implemented")
    
    async def start_monitoring(
        self,
        interval_seconds: int = 60,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Start continuous monitoring.
        
        Args:
            interval_seconds: Polling interval in seconds
            filters: Optional filters for trace selection
            **kwargs: Additional parameters
        """
        self._running = True
        self.logger.info(
            "Starting continuous monitoring",
            interval_seconds=interval_seconds,
            trace_source=self.trace_source,
        )
        
        while self._running:
            try:
                # Poll for new traces and evaluate
                # This is a simplified version - actual implementation would
                # track last evaluated timestamp and only evaluate new traces
                await self.evaluate_traces(filters=filters, **kwargs)
            except Exception as e:
                self.logger.error("Error in continuous monitoring", error=str(e))
            
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._running = False
        self.logger.info("Stopped continuous monitoring")
    
    def get_results(self) -> list[EvalResult]:
        """Get all evaluation results."""
        return self._evaluation_results.copy()
    
    def check_regressions(
        self,
        baseline_run: EvalResult,
        threshold: float = 0.01,
    ) -> list[dict[str, Any]]:
        """
        Check for regressions against baseline.
        
        Args:
            baseline_run: Baseline run to compare against
            threshold: Threshold for regression detection
            
        Returns:
            List of regression reports
        """
        regressions = []
        for run in self._evaluation_results:
            # Compare run against baseline
            from aieval.core.eval import Eval
            eval_ = Eval(name="regression_check", dataset=[], scorers=[])
            comparison = eval_.compare(baseline_run, run)
            
            if comparison.get("regressions"):
                regressions.append({
                    "run_id": run.run_id,
                    "regressions": comparison["regressions"],
                    "comparison": comparison,
                })
        
        return regressions
