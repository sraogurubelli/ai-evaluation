"""Task agent for managing task lifecycle and execution."""

from datetime import datetime
from typing import Any

from ai_evolution.agents.base import BaseEvaluationAgent
from ai_evolution.agents.experiment_agent import ExperimentAgent
from ai_evolution.tasks.manager import TaskManager
from ai_evolution.tasks.models import Task, TaskStatus, TaskResult


class TaskAgent(BaseEvaluationAgent):
    """Agent for task lifecycle management."""
    
    def __init__(
        self,
        config: dict[str, Any] | None = None,
        task_manager: TaskManager | None = None,
    ):
        """Initialize task agent."""
        super().__init__(config)
        self.task_manager = task_manager or TaskManager()
        self.experiment_agent = ExperimentAgent(config)
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run task operation based on query.
        
        Supported queries:
        - "create": Create a task
        - "execute": Execute a task
        - "get_status": Get task status
        - "cancel": Cancel a task
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "create":
            return await self.create_task(**kwargs)
        elif query == "execute":
            return await self.execute_task(**kwargs)
        elif query == "get_status":
            return await self.get_task_status(**kwargs)
        elif query == "cancel":
            return await self.cancel_task(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def create_task(
        self,
        experiment_name: str,
        config: dict[str, Any],
        **kwargs: Any,
    ) -> Task:
        """
        Create a new task.
        
        Args:
            experiment_name: Name of the experiment
            config: Experiment configuration
            **kwargs: Additional parameters
            
        Returns:
            Created task
        """
        self.logger.info(f"Creating task for experiment: {experiment_name}")
        
        task = await self.task_manager.create_task(
            experiment_name=experiment_name,
            config=config,
        )
        
        self.logger.info(f"Created task: {task.id}")
        return task
    
    async def execute_task(
        self,
        task_id: str,
        **kwargs: Any,
    ) -> TaskResult:
        """
        Execute a task.
        
        Args:
            task_id: Task ID to execute
            **kwargs: Additional parameters
            
        Returns:
            Task result
        """
        self.logger.info(f"Executing task: {task_id}")
        
        result = await self.task_manager.execute_task(task_id)
        
        self.logger.info(f"Task {task_id} completed successfully")
        return result
    
    async def get_task_status(
        self,
        task_id: str,
        **kwargs: Any,
    ) -> Task:
        """
        Get task status.
        
        Args:
            task_id: Task ID
            **kwargs: Additional parameters
            
        Returns:
            Task with current status
        """
        task = await self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        return task
    
    async def cancel_task(
        self,
        task_id: str,
        **kwargs: Any,
    ) -> Task:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID to cancel
            **kwargs: Additional parameters
            
        Returns:
            Cancelled task
        """
        self.logger.info(f"Cancelling task: {task_id}")
        
        task = await self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError(f"Cannot cancel task in status {task.status}")
        
        # Update status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        self.logger.info(f"Task {task_id} cancelled")
        return task
