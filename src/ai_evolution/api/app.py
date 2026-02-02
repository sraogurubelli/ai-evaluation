"""FastAPI application for AI Evolution Platform."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_evolution.api.models import (
    ExperimentConfigRequest,
    TaskResponse,
    TaskResultResponse,
    ExperimentRunResponse,
    ErrorResponse,
    HealthResponse,
    # Dataset Agent models
    DatasetLoadRequest,
    DatasetLoadResponse,
    DatasetValidateRequest,
    DatasetValidateResponse,
    DatasetListResponse,
    # Scorer Agent models
    ScorerCreateRequest,
    ScorerCreateResponse,
    ScorerScoreRequest,
    ScorerScoreResponse,
    ScorerListResponse,
    # Adapter Agent models
    AdapterCreateRequest,
    AdapterCreateResponse,
    AdapterGenerateRequest,
    AdapterGenerateResponse,
    AdapterListResponse,
    # Experiment Agent models
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentRunRequest,
    ExperimentRunResponse as ExperimentRunResponseNew,
    ExperimentCompareRequest,
    ExperimentCompareResponse,
    # Evaluation Agent models
    EvaluationRequest,
    EvaluationResponse,
)
from ai_evolution.tasks.manager import TaskManager
from ai_evolution.tasks.worker import TaskWorker
from ai_evolution.tasks.models import TaskStatus
from ai_evolution.agents import (
    DatasetAgent,
    ScorerAgent,
    AdapterAgent,
    ExperimentAgent,
    TaskAgent,
    EvaluationAgent,
)
from ai_evolution.core.types import DatasetItem

logger = structlog.get_logger(__name__)

# Global task manager and worker
task_manager: TaskManager | None = None
task_worker: TaskWorker | None = None
worker_task: asyncio.Task | None = None

# Global agents
dataset_agent: DatasetAgent | None = None
scorer_agent: ScorerAgent | None = None
adapter_agent: AdapterAgent | None = None
experiment_agent: ExperimentAgent | None = None
task_agent: TaskAgent | None = None
evaluation_agent: EvaluationAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global task_manager, task_worker, worker_task
    global dataset_agent, scorer_agent, adapter_agent, experiment_agent, task_agent, evaluation_agent
    
    # Startup
    logger.info("Starting AI Evolution Platform API")
    
    # Initialize database (optional - only if DATABASE_URL is set)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            from ai_evolution.db.session import init_db
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(
                "Database initialization failed (continuing without DB)",
                error=str(e),
                exc_info=True,
            )
    
    task_manager = TaskManager()
    task_worker = TaskWorker(task_manager, max_concurrent=3)
    
    # Initialize agents
    dataset_agent = DatasetAgent()
    scorer_agent = ScorerAgent()
    adapter_agent = AdapterAgent()
    experiment_agent = ExperimentAgent()
    task_agent = TaskAgent(task_manager=task_manager)
    evaluation_agent = EvaluationAgent()
    
    # Start background worker
    worker_task = asyncio.create_task(task_worker.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Evolution Platform API")
    if task_worker:
        await task_worker.stop()
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    
    # Close database connections
    if database_url:
        try:
            from ai_evolution.db.session import close_db
            await close_db()
        except Exception as e:
            logger.warning(
                "Database shutdown error",
                error=str(e),
                exc_info=True,
            )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AI Evolution API",
        description="Unified AI Evaluation and Experimentation Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        # Get task counts
        tasks = await task_manager.list_tasks(limit=1000)
        task_counts = {
            status.value: sum(1 for t in tasks if t.status == status)
            for status in TaskStatus
        }
        
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            tasks=task_counts,
        )
    
    @app.post("/experiments", response_model=TaskResponse, status_code=201)
    async def create_experiment(
        request: ExperimentConfigRequest,
        background_tasks: BackgroundTasks,
    ):
        """
        Create and optionally run an experiment.
        
        If run_async is True, the task will be queued for background execution.
        If False, the task will be executed synchronously (may take a long time).
        """
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        # Create task
        task = await task_manager.create_task(
            experiment_name=request.experiment_name,
            config=request.config,
        )
        
        # Execute task
        if request.run_async:
            # Queue for background execution (worker will pick it up)
            logger.info(
                "Task queued for async execution",
                task_id=task.id,
                experiment_name=request.experiment_name,
            )
        else:
            # Execute synchronously
            try:
                await task_manager.execute_task(task.id)
            except Exception as e:
                logger.error(
                    "Task execution failed",
                    task_id=task.id,
                    error=str(e),
                    exc_info=True,
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        return TaskResponse(**task.to_dict())
    
    @app.get("/tasks", response_model=list[TaskResponse])
    async def list_tasks(
        status: TaskStatus | None = None,
        limit: int = 100,
    ):
        """List tasks, optionally filtered by status."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        tasks = await task_manager.list_tasks(status=status, limit=limit)
        return [TaskResponse(**task.to_dict()) for task in tasks]
    
    @app.get("/tasks/{task_id}", response_model=TaskResponse)
    async def get_task(task_id: str):
        """Get task by ID."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        task = await task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return TaskResponse(**task.to_dict())
    
    @app.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
    async def get_task_result(task_id: str):
        """Get task result."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        task = await task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if not task.result:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} has no result yet (status: {task.status})",
            )
        
        return TaskResultResponse(**task.result.to_dict())
    
    @app.get("/tasks/{task_id}/run", response_model=ExperimentRunResponse)
    async def get_task_run(task_id: str):
        """Get experiment run from task result."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        task = await task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if not task.result:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} has no result yet (status: {task.status})",
            )
        
        return ExperimentRunResponse(**task.result.experiment_run.to_dict())
    
    @app.delete("/tasks/{task_id}", status_code=204)
    async def cancel_task(task_id: str):
        """Cancel a pending or running task."""
        if not task_manager:
            raise HTTPException(status_code=503, detail="Task manager not initialized")
        
        task = await task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task in status {task.status}",
            )
        
        # Update status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        return None
    
    # ============================================================================
    # Dataset Agent Endpoints
    # ============================================================================
    
    @app.post("/evaluate/dataset/load", response_model=DatasetLoadResponse, status_code=200)
    async def load_dataset(request: DatasetLoadRequest):
        """Load a dataset."""
        if not dataset_agent:
            raise HTTPException(status_code=503, detail="Dataset agent not initialized")
        
        try:
            dataset = await dataset_agent.load_dataset(
                dataset_type=request.dataset_type,
                path=request.path,
                index_file=request.index_file,
                base_dir=request.base_dir,
                filters=request.filters,
                offline=request.offline,
                actual_suffix=request.actual_suffix,
            )
            logger.info(
                "Dataset loaded",
                dataset_type=request.dataset_type,
                item_count=len(dataset),
            )
            return DatasetLoadResponse(
                item_count=len(dataset),
                items=[item.to_dict() for item in dataset],
            )
        except Exception as e:
            logger.error(
                "Error loading dataset",
                dataset_type=request.dataset_type,
                path=request.path,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate/dataset/validate", response_model=DatasetValidateResponse, status_code=200)
    async def validate_dataset(request: DatasetValidateRequest):
        """Validate dataset format."""
        if not dataset_agent:
            raise HTTPException(status_code=503, detail="Dataset agent not initialized")
        
        try:
            result = await dataset_agent.validate_dataset(
                dataset_type=request.dataset_type,
                path=request.path,
            )
            logger.info(
                "Dataset validated",
                dataset_type=request.dataset_type,
                path=request.path,
                valid=result.get("valid", False),
            )
            return DatasetValidateResponse(**result)
        except Exception as e:
            logger.error(
                "Error validating dataset",
                dataset_type=request.dataset_type,
                path=request.path,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/evaluate/dataset/list", response_model=DatasetListResponse, status_code=200)
    async def list_datasets(base_dir: str | None = None):
        """List available datasets."""
        if not dataset_agent:
            raise HTTPException(status_code=503, detail="Dataset agent not initialized")
        
        try:
            datasets = await dataset_agent.list_datasets(base_dir=base_dir)
            logger.info(
                "Datasets listed",
                base_dir=base_dir,
                count=len(datasets),
            )
            return DatasetListResponse(datasets=datasets)
        except Exception as e:
            logger.error(
                "Error listing datasets",
                base_dir=base_dir,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    # ============================================================================
    # Scorer Agent Endpoints
    # ============================================================================
    
    @app.post("/evaluate/scorer/create", response_model=ScorerCreateResponse, status_code=201)
    async def create_scorer(request: ScorerCreateRequest):
        """Create a scorer."""
        if not scorer_agent:
            raise HTTPException(status_code=503, detail="Scorer agent not initialized")
        
        try:
            scorer = await scorer_agent.create_scorer(
                scorer_type=request.scorer_type,
                name=request.name,
                **request.config,
            )
            logger.info(
                "Scorer created",
                scorer_id=scorer.name,
                scorer_type=request.scorer_type,
            )
            return ScorerCreateResponse(
                scorer_id=scorer.name,
                name=scorer.name,
                type=type(scorer).__name__,
            )
        except Exception as e:
            logger.error(
                "Error creating scorer",
                scorer_type=request.scorer_type,
                name=request.name,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate/scorer/score", response_model=ScorerScoreResponse, status_code=200)
    async def score_item(request: ScorerScoreRequest):
        """Score a single item."""
        if not scorer_agent:
            raise HTTPException(status_code=503, detail="Scorer agent not initialized")
        
        try:
            item = DatasetItem(**request.item)
            score = await scorer_agent.score_item(
                scorer=request.scorer_id,
                item=item,
                output=request.output,
            )
            return ScorerScoreResponse(score=score.to_dict())
        except Exception as e:
            logger.error(
                "Error scoring item",
                scorer_id=request.scorer_id,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/evaluate/scorer/list", response_model=ScorerListResponse, status_code=200)
    async def list_scorers():
        """List available scorers."""
        if not scorer_agent:
            raise HTTPException(status_code=503, detail="Scorer agent not initialized")
        
        try:
            result = await scorer_agent.list_scorers()
            return ScorerListResponse(**result)
        except Exception as e:
            logger.error(
                "Error listing scorers",
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    # ============================================================================
    # Adapter Agent Endpoints
    # ============================================================================
    
    @app.post("/evaluate/adapter/create", response_model=AdapterCreateResponse, status_code=201)
    async def create_adapter(request: AdapterCreateRequest):
        """Create an adapter."""
        if not adapter_agent:
            raise HTTPException(status_code=503, detail="Adapter agent not initialized")
        
        try:
            adapter = await adapter_agent.create_adapter(
                adapter_type=request.adapter_type,
                name=request.name,
                **request.config,
            )
            adapter_id = request.name or f"{request.adapter_type}_{id(adapter)}"
            logger.info(
                "Adapter created",
                adapter_id=adapter_id,
                adapter_type=request.adapter_type,
            )
            return AdapterCreateResponse(
                adapter_id=adapter_id,
                type=type(adapter).__name__,
            )
        except Exception as e:
            logger.error(
                "Error creating adapter",
                adapter_type=request.adapter_type,
                name=request.name,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate/adapter/generate", response_model=AdapterGenerateResponse, status_code=200)
    async def generate_output(request: AdapterGenerateRequest):
        """Generate output using adapter."""
        if not adapter_agent:
            raise HTTPException(status_code=503, detail="Adapter agent not initialized")
        
        try:
            output = await adapter_agent.generate(
                adapter=request.adapter_id,
                input_data=request.input_data,
                model=request.model,
                **request.config,
            )
            return AdapterGenerateResponse(output=output)
        except Exception as e:
            logger.error(
                "Error generating output",
                adapter_id=request.adapter_id,
                model=request.model,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/evaluate/adapter/list", response_model=AdapterListResponse, status_code=200)
    async def list_adapters():
        """List available adapters."""
        if not adapter_agent:
            raise HTTPException(status_code=503, detail="Adapter agent not initialized")
        
        try:
            result = await adapter_agent.list_adapters()
            return AdapterListResponse(**result)
        except Exception as e:
            logger.error(
                "Error listing adapters",
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    # ============================================================================
    # Experiment Agent Endpoints
    # ============================================================================
    
    @app.post("/evaluate/experiment/create", response_model=ExperimentCreateResponse, status_code=201)
    async def create_experiment_agent(request: ExperimentCreateRequest):
        """Create an experiment."""
        if not experiment_agent:
            raise HTTPException(status_code=503, detail="Experiment agent not initialized")
        
        try:
            experiment = await experiment_agent.create_experiment(
                name=request.name,
                dataset_config=request.dataset_config,
                scorers_config=request.scorers_config,
                experiment_id=request.experiment_id,
            )
            logger.info(
                "Experiment created",
                experiment_id=experiment.experiment_id,
                name=experiment.name,
                dataset_size=len(experiment.dataset),
                scorer_count=len(experiment.scorers),
            )
            return ExperimentCreateResponse(
                experiment_id=experiment.experiment_id,
                name=experiment.name,
                dataset_size=len(experiment.dataset),
                scorer_count=len(experiment.scorers),
            )
        except Exception as e:
            logger.error(
                "Error creating experiment",
                name=request.name,
                experiment_id=request.experiment_id,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate/experiment/run", response_model=ExperimentRunResponseNew, status_code=200)
    async def run_experiment_agent(request: ExperimentRunRequest):
        """Run an experiment."""
        if not experiment_agent:
            raise HTTPException(status_code=503, detail="Experiment agent not initialized")
        
        try:
            run = await experiment_agent.run_experiment(
                experiment=request.experiment_id,
                adapter_config=request.adapter_config,
                model=request.model,
                concurrency_limit=request.concurrency_limit,
            )
            logger.info(
                "Experiment run completed",
                experiment_id=request.experiment_id,
                run_id=run.run_id,
                model=request.model,
            )
            return ExperimentRunResponseNew(**run.to_dict())
        except Exception as e:
            logger.error(
                "Error running experiment",
                experiment_id=request.experiment_id,
                model=request.model,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/evaluate/experiment/compare", response_model=ExperimentCompareResponse, status_code=200)
    async def compare_runs(request: ExperimentCompareRequest):
        """Compare experiment runs."""
        if not experiment_agent:
            raise HTTPException(status_code=503, detail="Experiment agent not initialized")
        
        try:
            result = await experiment_agent.compare_runs(
                run1=request.run1_id,
                run2=request.run2_id,
            )
            logger.info(
                "Runs compared",
                run1_id=request.run1_id,
                run2_id=request.run2_id,
            )
            return ExperimentCompareResponse(comparison=result)
        except Exception as e:
            logger.error(
                "Error comparing runs",
                run1_id=request.run1_id,
                run2_id=request.run2_id,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    # ============================================================================
    # Task Agent Endpoints (Enhanced)
    # ============================================================================
    
    @app.post("/evaluate/task/create", response_model=TaskResponse, status_code=201)
    async def create_task_agent(
        experiment_name: str,
        config: dict[str, Any],
    ):
        """Create evaluation task."""
        if not task_agent:
            raise HTTPException(status_code=503, detail="Task agent not initialized")
        
        try:
            task = await task_agent.create_task(
                experiment_name=experiment_name,
                config=config,
            )
            logger.info(
                "Task created",
                task_id=task.id,
                experiment_name=experiment_name,
            )
            return TaskResponse(**task.to_dict())
        except Exception as e:
            logger.error(
                "Error creating task",
                experiment_name=experiment_name,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/evaluate/task/{task_id}", response_model=TaskResponse)
    async def get_task_agent(task_id: str):
        """Get task status."""
        if not task_agent:
            raise HTTPException(status_code=503, detail="Task agent not initialized")
        
        try:
            task = await task_agent.get_task_status(task_id=task_id)
            return TaskResponse(**task.to_dict())
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(
                "Error getting task",
                task_id=task_id,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/evaluate/task/{task_id}", status_code=200)
    async def cancel_task_agent(task_id: str):
        """Cancel a task."""
        if not task_agent:
            raise HTTPException(status_code=503, detail="Task agent not initialized")
        
        try:
            task = await task_agent.cancel_task(task_id=task_id)
            return TaskResponse(**task.to_dict())
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(
                "Error cancelling task",
                task_id=task_id,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    # ============================================================================
    # Unified Evaluation Endpoint
    # ============================================================================
    
    @app.post("/evaluate/unified", response_model=EvaluationResponse, status_code=200)
    async def unified_evaluation(request: EvaluationRequest):
        """Unified evaluation endpoint (like /chat/unified in ml-infra)."""
        if not evaluation_agent:
            raise HTTPException(status_code=503, detail="Evaluation agent not initialized")
        
        try:
            # Get normalized models list
            models_list = request.get_models_list()
            
            result = await evaluation_agent.evaluate(
                experiment_name=request.experiment_name,
                dataset_config=request.dataset_config,
                scorers_config=request.scorers_config,
                adapter_config=request.adapter_config,
                model=request.model,  # For backward compatibility
                models=request.models,  # New multi-model support
                concurrency_limit=request.concurrency_limit,
                run_async=request.run_async,
            )
            
            if request.run_async:
                # Return task
                task = result
                return EvaluationResponse(
                    task_id=task.id,
                    run_id=None,
                    runs=None,
                    experiment_id=task.experiment_name,
                    scores=None,
                    comparison=None,
                    metadata=task.meta,
                )
            else:
                # Handle single or multiple runs
                if isinstance(result, list):
                    # Multiple models - return comparison
                    from ai_evolution.sdk.comparison import compare_multiple_runs
                    
                    runs = result
                    comparison = compare_multiple_runs(runs, models_list)
                    
                    return EvaluationResponse(
                        task_id=None,
                        run_id=None,  # No single run_id for multiple models
                        runs=[run.to_dict() for run in runs],
                        experiment_id=runs[0].experiment_id if runs else request.experiment_name,
                        scores=None,  # Scores are in individual runs
                        comparison=comparison,
                        metadata={"model_count": len(runs)},
                    )
                else:
                    # Single model - backward compatibility
                    run = result
                    # Get metadata from run, handling both 'metadata' and 'meta' attributes
                    run_metadata = getattr(run, 'metadata', None) or getattr(run, 'meta', None) or {}
                    return EvaluationResponse(
                        task_id=None,
                        run_id=run.run_id,
                        runs=None,
                        experiment_id=run.experiment_id,
                        scores=[score.to_dict() for score in run.scores],
                        comparison=None,
                        metadata=run_metadata,
                    )
        except Exception as e:
            logger.error(
                "Error in unified evaluation",
                experiment_name=request.experiment_name,
                model=request.model,
                models=request.models,
                error=str(e),
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(
            "Unhandled exception",
            path=request.url.path if hasattr(request, 'url') else None,
            method=request.method if hasattr(request, 'method') else None,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )
    
    return app


# Create app instance for uvicorn import string support
app = create_app()
