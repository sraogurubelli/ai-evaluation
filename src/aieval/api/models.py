"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aieval.tasks.models import TaskStatus


# Existing models
class EvalConfigRequest(BaseModel):
    """Request to create/run an eval."""

    eval_name: str = Field(..., description="Name of the eval")
    config: dict[str, Any] = Field(..., description="Eval configuration (YAML-like structure)")
    run_async: bool = Field(default=False, description="Run asynchronously (returns immediately)")
    agent_id: str | None = Field(None, description="Unique identifier for the agent (for grouping runs)")
    agent_name: str | None = Field(None, description="Display name for the agent")
    agent_version: str | None = Field(None, description="Display version for the agent")


class TaskResponse(BaseModel):
    """Task response model."""

    id: str
    eval_name: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResultResponse(BaseModel):
    """Task result response model."""

    task_id: str
    run: dict[str, Any]
    execution_time_seconds: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    """Run response model."""

    eval_id: str
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


class AdapterRegisterRequest(BaseModel):
    """Request to register a custom adapter dynamically."""
    
    adapter_type: str = Field(..., description="Unique identifier for the adapter type")
    module_path: str = Field(..., description="Python module path (e.g., 'my_team.adapters')")
    class_name: str = Field(..., description="Class name of the adapter")
    factory_kwargs: dict[str, Any] = Field(default_factory=dict, description="Optional default kwargs for adapter constructor")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata about the adapter")


class AdapterRegisterResponse(BaseModel):
    """Response from registering an adapter."""
    
    adapter_type: str
    message: str


# Experiment Agent Models (field names kept for backward compatibility; user-facing: Eval)
class ExperimentCreateRequest(BaseModel):
    """Request to create an eval."""

    name: str = Field(..., description="Name of the eval")
    dataset_config: dict[str, Any] = Field(..., description="Dataset configuration")
    scorers_config: list[dict[str, Any]] = Field(..., description="List of scorer configurations")
    experiment_id: str | None = Field(None, description="Optional eval ID")


class ExperimentCreateResponse(BaseModel):
    """Response from creating an eval."""
    
    experiment_id: str
    name: str
    dataset_size: int
    scorer_count: int


class ExperimentRunRequest(BaseModel):
    """Request to run an eval."""
    
    experiment_id: str = Field(..., description="Eval ID")
    adapter_config: dict[str, Any] = Field(..., description="Adapter configuration")
    model: str | None = Field(None, description="Optional model name")
    concurrency_limit: int = Field(default=5, description="Concurrency limit")


class ExperimentRunResponse(BaseModel):
    """Response from running an eval (run result)."""
    
    run_id: str
    experiment_id: str
    scores: list[dict[str, Any]]
    metadata: dict[str, Any]


class ExperimentCompareRequest(BaseModel):
    """Request to compare runs."""
    
    run1_id: str = Field(..., description="First run ID")
    run2_id: str = Field(..., description="Second run ID")


class ExperimentCompareResponse(BaseModel):
    """Response from comparing runs."""
    
    comparison: dict[str, Any]


# Agents and runs (consolidation per agent)
class AgentSummaryResponse(BaseModel):
    """Summary of an agent that has at least one run."""
    
    agent_id: str
    agent_name: str | None = None
    last_run_at: str | None = None
    run_count: int = 0


class AgentRunSummaryResponse(BaseModel):
    """Summary of a single run for an agent."""
    
    run_id: str
    task_id: str | None = None
    created_at: str
    model: str | None = None
    total: int = 0
    passed: int = 0
    failed: int = 0
    report_url: str | None = None


class PushRunRequest(BaseModel):
    """Request to push a run from consumer (e.g. CI) so it appears under an agent."""
    
    run_id: str = Field(..., description="Run ID")
    eval_id: str = Field(..., description="Eval ID")
    dataset_id: str = Field(..., description="Dataset ID")
    scores: list[dict[str, Any]] = Field(..., description="Scores")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Run metadata (should include agent_id)")


# Evaluation Agent Models (Unified)
class EvaluationRequest(BaseModel):
    """Request for unified evaluation."""
    
    eval_name: str = Field(..., description="Name of the eval")
    dataset_config: dict[str, Any] = Field(..., description="Dataset configuration")
    scorers_config: list[dict[str, Any]] = Field(..., description="List of scorer configurations (metrics/scorers)")
    adapter_config: dict[str, Any] = Field(..., description="Adapter configuration")
    models: list[str] | None = Field(None, description="List of models to evaluate (one run per model)")
    model: str | None = Field(None, description="[Deprecated] Single model name (use 'models' instead)")
    concurrency_limit: int = Field(default=5, description="Concurrency limit")
    run_async: bool = Field(default=False, description="Run asynchronously")
    agent_id: str | None = Field(None, description="Unique identifier for the agent (for grouping runs)")
    agent_name: str | None = Field(None, description="Display name for the agent")
    agent_version: str | None = Field(None, description="Display version for the agent")
    
    def get_models_list(self) -> list[str | None]:
        """Normalize models input - prioritize models over model for backward compatibility."""
        if self.models:
            return self.models
        elif self.model:
            return [self.model]
        else:
            return [None]  # Use adapter default


class EvaluationResponse(BaseModel):
    """Response from unified evaluation."""
    
    task_id: str | None = Field(None, description="Task ID (if run_async=True)")
    runs: list[dict[str, Any]] | None = Field(None, description="Multiple runs (one per model, if multiple models)")
    run_id: str | None = Field(None, description="Single run ID (backward compatibility, if single model)")
    eval_id: str
    scores: list[dict[str, Any]] | None = Field(None, description="Scores from single run (if run_async=False and single model)")
    comparison: dict[str, Any] | None = Field(None, description="Model comparison metrics (if multiple models)")
    metadata: dict[str, Any] = Field(default_factory=dict)


# Guardrail Validation Models
class PromptValidationRequest(BaseModel):
    """Request to validate a prompt."""
    
    prompt: str = Field(..., description="Prompt text to validate")
    task_id: str | None = Field(None, description="Optional task context")
    policy_name: str | None = Field(None, description="Policy name (if None, uses all policies)")
    rule_ids: list[str] | None = Field(None, description="Specific rule IDs to check")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ResponseValidationRequest(BaseModel):
    """Request to validate a response."""
    
    prompt: str = Field(..., description="Original prompt")
    response: str = Field(..., description="Response text to validate")
    context: str | None = Field(None, description="RAG context (for hallucination checks)")
    task_id: str | None = Field(None, description="Optional task context")
    policy_name: str | None = Field(None, description="Policy name (if None, uses all policies)")
    rule_ids: list[str] | None = Field(None, description="Specific rule IDs to check")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchValidationRequest(BaseModel):
    """Request for batch validation."""
    
    items: list[dict[str, Any]] = Field(..., description="List of items to validate")
    task_id: str | None = Field(None, description="Optional task context")
    policy_name: str | None = Field(None, description="Policy name")


class RuleResultResponse(BaseModel):
    """Result from a single rule evaluation."""
    
    rule_id: str
    rule_type: str
    passed: bool
    score: float
    action: str
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationResultResponse(BaseModel):
    """Response from validation."""
    
    passed: bool
    blocked: bool
    rule_results: list[RuleResultResponse]
    inference_id: str | None = Field(None, description="Inference ID if saved to database")


class BatchValidationResponse(BaseModel):
    """Response from batch validation."""
    
    results: list[ValidationResultResponse]
    total: int
    passed: int
    failed: int
    blocked: int
