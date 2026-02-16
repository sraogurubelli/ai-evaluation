"""Evaluation scheduler for scheduled trace evaluation."""

from typing import Any, Callable
import asyncio
import structlog
from datetime import datetime, timedelta
from croniter import croniter

from aieval.monitoring.evaluator import ContinuousEvaluator

logger = structlog.get_logger(__name__)

# Try to import croniter
try:
    import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    logger.warning("croniter not available. Install with: pip install croniter")


class EvaluationScheduler:
    """
    Scheduler for running evaluations on a schedule (cron-like).
    """
    
    def __init__(self):
        """Initialize scheduler."""
        self.logger = structlog.get_logger(__name__)
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False
    
    def schedule_evaluation(
        self,
        name: str,
        cron_expression: str,
        evaluator: ContinuousEvaluator,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Schedule an evaluation to run on a cron schedule.
        
        Args:
            name: Schedule name
            cron_expression: Cron expression (e.g., "0 * * * *" for hourly)
            evaluator: ContinuousEvaluator instance
            filters: Optional filters for trace selection
            **kwargs: Additional parameters
        """
        if not CRONITER_AVAILABLE:
            raise ImportError("croniter is required for scheduling. Install with: pip install croniter")
        
        if name in self._tasks:
            raise ValueError(f"Schedule '{name}' already exists")
        
        # Create scheduled task
        async def scheduled_task():
            while self._running:
                try:
                    # Calculate next run time
                    now = datetime.now()
                    cron = croniter(cron_expression, now)
                    next_run = cron.get_next(datetime)
                    wait_seconds = (next_run - now).total_seconds()
                    
                    self.logger.info(
                        "Scheduled evaluation",
                        name=name,
                        next_run=next_run.isoformat(),
                        wait_seconds=wait_seconds,
                    )
                    
                    await asyncio.sleep(wait_seconds)
                    
                    # Run evaluation
                    self.logger.info("Running scheduled evaluation", name=name)
                    await evaluator.evaluate_traces(filters=filters, **kwargs)
                except Exception as e:
                    self.logger.error(
                        "Error in scheduled evaluation",
                        name=name,
                        error=str(e),
                    )
        
        task = asyncio.create_task(scheduled_task())
        self._tasks[name] = task
        self.logger.info("Scheduled evaluation", name=name, cron=cron_expression)
    
    def start(self) -> None:
        """Start scheduler."""
        self._running = True
        self.logger.info("Evaluation scheduler started")
    
    def stop(self) -> None:
        """Stop scheduler and cancel all tasks."""
        self._running = False
        for name, task in self._tasks.items():
            task.cancel()
        self._tasks.clear()
        self.logger.info("Evaluation scheduler stopped")
    
    def remove_schedule(self, name: str) -> None:
        """Remove a scheduled evaluation."""
        if name in self._tasks:
            self._tasks[name].cancel()
            del self._tasks[name]
            self.logger.info("Removed schedule", name=name)
