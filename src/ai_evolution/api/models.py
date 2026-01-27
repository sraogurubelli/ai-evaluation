"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ai_evolution.tasks.models import TaskStatus


# Existing models
class ExperimentConfigRequest(BaseModel):
    """Request to create/run an experiment."""
    
    experiment_name: str = Field(..., description="Name of the experiment")
    config: dict[str, Any] = Field(..., description="Experiment configuration (YAML-like structure)")
    run_async: bool = Field(default=False, description="Run asynchronously (returns immediately)")


class TaskResponse(BaseModel):
    """Task response model."""
    
    id: str
    experiment_name: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResultResponse(BaseModel):
    """Task result response model."""
    
    task_id: str
    experiment_run: dict[str, Any]
    execution_time_seconds: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentRunResponse(BaseModel):
    """Experiment run response model."""
    
    experiment_id: str
    run_id: str
    dataset_id: str
    scores: list[dict[str, Any]]
    metadata: dict[str, Any]
    created_at: str


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    tasks: dict[str, int] = Field(description="Task counts by status")


# Dataset Agent Models
class DatasetLoadRequest(BaseModel):
    """Request to load a dataset."""
    
    dataset_type: str = Field(..., description="Type of dataset (jsonl, index_csv, function)")
    path: str | None = Field(None, description="Path to dataset file")
    index_file: str | None = Field(None, description="Path to index CSV file (for index_csv)")
    base_dir: str | None = Field(None, description="Base directory for index_csv datasets")
    filters: dict[str, Any] = Field(default_factory=dict, description="Filters for index_csv datasets")
    offline: bool = Field(default=False, description="Use offline mode for index_csv")
    actual_suffix: str = Field(default="actual", description="Suffix for actual files")


class DatasetLoadResponse(BaseModel):
    """Response from loading a dataset."""
    
    item_count: int
    items: list[dict[str, Any]]


class DatasetValidateRequest(BaseModel):
    """Request to validate a dataset."""
    
    dataset_type: str | None = Field(None, description="Type of dataset (if loading from file)")
    path: str | None = Field(None, description="Path to dataset file (if loading from file)")


class DatasetValidateResponse(BaseModel):
    """Response from dataset validation."""
    
    valid: bool
    item_count: int
    issues: list[str]


class DatasetListResponse(BaseModel):
    """Response from listing datasets."""
    
    datasets: list[dict[str, Any]]


# Scorer Agent Models
class ScorerCreateRequest(BaseModel):
    """Request to create a scorer."""
    
    scorer_type: str = Field(..., description="Type of scorer")
    name: str | None = Field(None, description="Optional name for the scorer")
    config: dict[str, Any] = Field(default_factory=dict, description="Scorer-specific configuration")


class ScorerCreateResponse(BaseModel):
    """Response from creating a scorer."""
    
    scorer_id: str
    name: str
    type: str


class ScorerScoreRequest(BaseModel):
    """Request to score an item."""
    
    scorer_id: str = Field(..., description="Scorer ID (if cached) or scorer type")
    item: dict[str, Any] = Field(..., description="Dataset item to score")
    output: Any | None = Field(None, description="Generated output (if not in item)")


class ScorerScoreResponse(BaseModel):
    """Response from scoring an item."""
    
    score: dict[str, Any]


class ScorerListResponse(BaseModel):
    """Response from listing scorers."""
    
    cached: list[dict[str, Any]]
    available_types: list[dict[str, Any]]


# Adapter Agent Models
class AdapterCreateRequest(BaseModel):
    """Request to create an adapter."""
    
    adapter_type: str = Field(..., description="Type of adapter (http, ml_infra, langfuse)")
    name: str | None = Field(None, description="Optional name for the adapter")
    config: dict[str, Any] = Field(default_factory=dict, description="Adapter-specific configuration")


class AdapterCreateResponse(BaseModel):
    """Response from creating an adapter."""
    
    adapter_id: str
    type: str


class AdapterGenerateRequest(BaseModel):
    """Request to generate output using adapter."""
    
    adapter_id: str = Field(..., description="Adapter ID (if cached) or adapter type")
    input_data: dict[str, Any] = Field(..., description="Input data for generation")
    model: str | None = Field(None, description="Optional model name")
    config: dict[str, Any] = Field(default_factory=dict, description="Adapter-specific configuration")


class AdapterGenerateResponse(BaseModel):
    """Response from generating output."""
    
    output: Any


class AdapterListResponse(BaseModel):
    """Response from listing adapters."""
    
    cached: list[dict[str, Any]]
    available_types: list[dict[str, Any]]


# Experiment Agent Models
class ExperimentCreateRequest(BaseModel):
    """Request to create an experiment."""
    
    name: str = Field(..., description="Experiment name")
    dataset_config: dict[str, Any] = Field(..., description="Dataset configuration")
    scorers_config: list[dict[str, Any]] = Field(..., description="List of scorer configurations")
    experiment_id: str | None = Field(None, description="Optional experiment ID")


class ExperimentCreateResponse(BaseModel):
    """Response from creating an experiment."""
    
    experiment_id: str
    name: str
    dataset_size: int
    scorer_count: int


class ExperimentRunRequest(BaseModel):
    """Request to run an experiment."""
    
    experiment_id: str = Field(..., description="Experiment ID")
    adapter_config: dict[str, Any] = Field(..., description="Adapter configuration")
    model: str | None = Field(None, description="Optional model name")
    concurrency_limit: int = Field(default=5, description="Concurrency limit")


class ExperimentRunResponse(BaseModel):
    """Response from running an experiment."""
    
    run_id: str
    experiment_id: str
    scores: list[dict[str, Any]]
    metadata: dict[str, Any]


class ExperimentCompareRequest(BaseModel):
    """Request to compare experiment runs."""
    
    run1_id: str = Field(..., description="First run ID")
    run2_id: str = Field(..., description="Second run ID")


class ExperimentCompareResponse(BaseModel):
    """Response from comparing runs."""
    
    comparison: dict[str, Any]


# Evaluation Agent Models (Unified)
class EvaluationRequest(BaseModel):
    """Request for unified evaluation."""
    
    experiment_name: str = Field(..., description="Name of the experiment")
    dataset_config: dict[str, Any] = Field(..., description="Dataset configuration")
    scorers_config: list[dict[str, Any]] = Field(..., description="List of scorer configurations")
    adapter_config: dict[str, Any] = Field(..., description="Adapter configuration")
    model: str | None = Field(None, description="Optional model name")
    concurrency_limit: int = Field(default=5, description="Concurrency limit")
    run_async: bool = Field(default=False, description="Run asynchronously")


class EvaluationResponse(BaseModel):
    """Response from unified evaluation."""
    
    task_id: str | None = Field(None, description="Task ID (if run_async=True)")
    run_id: str | None = Field(None, description="Run ID (if run_async=False)")
    experiment_id: str
    scores: list[dict[str, Any]] | None = Field(None, description="Scores (if run_async=False)")
    metadata: dict[str, Any]
