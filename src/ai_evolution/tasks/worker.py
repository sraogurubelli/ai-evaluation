"""Background worker for executing tasks."""

import asyncio
import logging
from typing import Any

from ai_evolution.tasks.manager import TaskManager
from ai_evolution.tasks.models import TaskStatus

logger = logging.getLogger(__name__)


class TaskWorker:
    """Background worker that executes tasks."""
    
    def __init__(self, task_manager: TaskManager, max_concurrent: int = 3):
        """
        Initialize task worker.
        
        Args:
            task_manager: Task manager instance
            max_concurrent: Maximum concurrent task executions
        """
        self.task_manager = task_manager
        self.max_concurrent = max_concurrent
        self._running = False
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        logger.info("Task worker started")
        
        while self._running:
            try:
                # Get pending tasks
                pending_tasks = await self.task_manager.list_tasks(
                    status=TaskStatus.PENDING,
                    limit=self.max_concurrent,
                )
                
                if not pending_tasks:
                    # No pending tasks, wait a bit
                    await asyncio.sleep(1)
                    continue
                
                # Execute tasks concurrently (up to max_concurrent)
                tasks_to_run = pending_tasks[:self.max_concurrent]
                await asyncio.gather(
                    *[self._execute_task(task.id) for task in tasks_to_run],
                    return_exceptions=True,
                )
                
            except Exception as e:
                logger.error(f"Error in task worker loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        logger.info("Task worker stopped")
    
    async def _execute_task(self, task_id: str) -> None:
        """Execute a single task."""
        async with self._semaphore:
            try:
                await self.task_manager.execute_task(task_id)
            except Exception as e:
                logger.error(f"Failed to execute task {task_id}: {e}", exc_info=True)
