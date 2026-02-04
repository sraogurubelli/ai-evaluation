"""Task manager for executing experiments."""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Any

from aieval.tasks.models import Task, TaskStatus, TaskResult
from aieval.core.experiment import Experiment
from aieval.core.types import DatasetItem
from aieval.datasets import load_jsonl_dataset, load_index_csv_dataset
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer
from aieval.scorers.dashboard import DashboardQualityScorer
from aieval.scorers.knowledge_graph import KnowledgeGraphQualityScorer

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages task execution and storage."""
    
    def __init__(self):
        """Initialize task manager."""
        self.tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()
    
    async def create_task(
        self,
        experiment_name: str,
        config: dict[str, Any],
    ) -> Task:
        """
        Create a new task.
        
        Args:
            experiment_name: Name of the experiment
            config: Experiment configuration
            
        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            experiment_name=experiment_name,
            config=config,
            status=TaskStatus.PENDING,
        )
        
        async with self._lock:
            self.tasks[task_id] = task
        
        logger.info(f"Created task {task_id} for experiment {experiment_name}")
        return task
    
    async def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        async with self._lock:
            return self.tasks.get(task_id)
    
    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        limit: int = 100,
    ) -> list[Task]:
        """List tasks, optionally filtered by status."""
        async with self._lock:
            tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def execute_task(self, task_id: str) -> TaskResult:
        """
        Execute a task.
        
        Args:
            task_id: Task ID to execute
            
        Returns:
            Task result
            
        Raises:
            ValueError: If task not found
            RuntimeError: If task execution fails
        """
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task {task_id} is not pending (status: {task.status})")
        
        # Update status
        async with self._lock:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
        
        try:
            # Load dataset
            dataset = self._load_dataset(task.config)
            
            # Create scorers
            scorers = self._create_scorers(task.config)
            
            # Create adapter
            adapter = self._create_adapter(task.config)
            
            # Create experiment
            experiment = Experiment(
                name=task.experiment_name,
                dataset=dataset,
                scorers=scorers,
            )
            
            # Get execution config
            execution_config = task.config.get("execution", {})
            concurrency_limit = execution_config.get("concurrency_limit", 5)
            models = task.config.get("models", [None])
            
            # Run experiment for first model (can extend to multiple later)
            model = models[0] if models else None
            
            # Agent identity for grouping runs (optional)
            run_kwargs: dict[str, Any] = {}
            if task.config.get("agent_id") is not None:
                run_kwargs["agent_id"] = task.config["agent_id"]
            if task.config.get("agent_name") is not None:
                run_kwargs["agent_name"] = task.config["agent_name"]
            if task.config.get("agent_version") is not None:
                run_kwargs["agent_version"] = task.config["agent_version"]
            
            import time
            start_time = time.time()
            
            run = await experiment.run(
                adapter=adapter,
                model=model,
                concurrency_limit=concurrency_limit,
                **run_kwargs,
            )
            
            execution_time = time.time() - start_time
            
            # Create result
            result = TaskResult(
                task_id=task_id,
                experiment_run=run,
                execution_time_seconds=execution_time,
                metadata={
                    "model": model,
                    "dataset_size": len(dataset),
                    "scorers": [s.name for s in scorers],
                },
            )
            
            # Update task
            async with self._lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
            
            logger.info(f"Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            async with self._lock:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = str(e)
            raise RuntimeError(f"Task execution failed: {e}") from e
    
    def _load_dataset(self, config: dict[str, Any]) -> list[DatasetItem]:
        """Load dataset from config."""
        dataset_config = config.get("dataset", {})
        dataset_type = dataset_config.get("type", "jsonl")
        
        if dataset_type == "jsonl":
            path = dataset_config["path"]
            return load_jsonl_dataset(path)
        elif dataset_type == "index_csv":
            path = dataset_config.get("index_file") or dataset_config["path"]
            base_dir = dataset_config.get("base_dir", "benchmarks/datasets")
            filters = dataset_config.get("filters", {})
            return load_index_csv_dataset(
                index_file=path,
                base_dir=base_dir,
                entity_type=filters.get("entity_type"),
                operation_type=filters.get("operation_type"),
                test_id=filters.get("test_id"),
                offline=dataset_config.get("offline", False),
                actual_suffix=dataset_config.get("actual_suffix", "actual"),
            )
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    def _create_scorers(self, config: dict[str, Any]) -> list:
        """Create scorers from config."""
        scorers_config = config.get("scorers", [])
        scorers = []
        
        for scorer_config in scorers_config:
            scorer_type = scorer_config.get("type")
            
            if scorer_type == "deep_diff":
                version = scorer_config.get("version", "v3")
                entity_type = scorer_config.get("entity_type")
                validation_func = scorer_config.get("validation_func")
                
                scorer = DeepDiffScorer(
                    name=f"deep_diff_{version}",
                    eval_id=f"deep_diff_{version}.v1",
                    version=version,
                    entity_type=entity_type,
                    validation_func=validation_func,
                )
                scorers.append(scorer)
            
            elif scorer_type == "schema_validation":
                validation_func = scorer_config.get("validation_func")
                scorer = SchemaValidationScorer(validation_func=validation_func)
                scorers.append(scorer)
            
            elif scorer_type == "dashboard_quality":
                scorer = DashboardQualityScorer()
                scorers.append(scorer)
            
            elif scorer_type == "kg_quality":
                scorer = KnowledgeGraphQualityScorer()
                scorers.append(scorer)
        
        return scorers
    
    def _create_adapter(self, config: dict[str, Any]):
        """Create adapter from config."""
        adapter_config = config.get("adapter", {})
        adapter_type = adapter_config.get("type", "http")  # Default to http adapter
        
        import os
        from aieval.adapters.http import HTTPAdapter
        
        if adapter_type == "http" or adapter_type == "rest":
            # Generic HTTP adapter (recommended)
            return HTTPAdapter(
                base_url=adapter_config.get("base_url", os.getenv("CHAT_BASE_URL", "http://localhost:8000")),
                auth_token=adapter_config.get("auth_token", os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")),
                context_field_name=adapter_config.get("context_field_name", "context"),
                context_data=adapter_config.get("context_data", {}),
                endpoint_mapping=adapter_config.get("endpoint_mapping", {}),
                default_endpoint=adapter_config.get("default_endpoint", "/chat/platform"),
                response_format=adapter_config.get("response_format", "json"),
                yaml_extraction_path=adapter_config.get("yaml_extraction_path"),
                sse_completion_events=adapter_config.get("sse_completion_events"),
            )
        elif adapter_type == "ml_infra":
            # Deprecated: Use "http" adapter type with ml-infra configuration
            import warnings
            warnings.warn(
                "ml_infra adapter type is deprecated. Use 'http' adapter type instead.",
                DeprecationWarning,
                stacklevel=2
            )
            
            # Use HTTPAdapter with ml-infra configuration
            return HTTPAdapter(
                base_url=adapter_config.get("base_url", os.getenv("CHAT_BASE_URL", "http://localhost:8000")),
                auth_token=adapter_config.get("auth_token", os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")),
                context_field_name="harness_context",
                context_data={
                    "account_id": adapter_config.get("account_id", os.getenv("ACCOUNT_ID", "default")),
                    "org_id": adapter_config.get("org_id", os.getenv("ORG_ID", "default")),
                    "project_id": adapter_config.get("project_id", os.getenv("PROJECT_ID", "default")),
                },
                endpoint_mapping={
                    "dashboard": "/chat/dashboard",
                    "knowledge_graph": "/chat/knowledge-graph",
                },
                default_endpoint="/chat/platform",
                yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
                sse_completion_events=["dashboard_complete", "kg_complete"],
            )
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
