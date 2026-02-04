"""Fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient
from aieval.api.app import app, adapter_agent, dataset_agent, scorer_agent, experiment_agent, task_agent, evaluation_agent
from aieval.agents import AdapterAgent, DatasetAgent, ScorerAgent, ExperimentAgent, TaskAgent, EvaluationAgent
from aieval.tasks.manager import TaskManager


@pytest.fixture(autouse=True)
def initialize_agents():
    """Initialize agents for testing (since TestClient doesn't run lifespan events)."""
    global adapter_agent, dataset_agent, scorer_agent, experiment_agent, task_agent, evaluation_agent
    
    # Import the global variables from app module
    import aieval.api.app as app_module
    
    # Initialize agents if not already initialized
    if app_module.adapter_agent is None:
        app_module.adapter_agent = AdapterAgent()
    if app_module.dataset_agent is None:
        app_module.dataset_agent = DatasetAgent()
    if app_module.scorer_agent is None:
        app_module.scorer_agent = ScorerAgent()
    if app_module.experiment_agent is None:
        app_module.experiment_agent = ExperimentAgent()
    if app_module.task_agent is None:
        task_manager = TaskManager()
        app_module.task_agent = TaskAgent(task_manager=task_manager)
    if app_module.evaluation_agent is None:
        app_module.evaluation_agent = EvaluationAgent()
    
    yield
    
    # Cleanup (optional - tests can share the same agents)


@pytest.fixture
def client():
    """Create test client for FastAPI app. Uses context manager so lifespan runs."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_dataset_config():
    """Sample dataset configuration for tests."""
    return {
        "dataset_type": "index_csv",
        "index_file": "benchmarks/datasets/index.csv",
        "base_dir": "benchmarks/datasets",
        "filters": {
            "entity_type": "pipeline",
            "operation_type": "create",
        },
    }


@pytest.fixture
def sample_adapter_config():
    """Sample adapter configuration for tests."""
    return {
        "adapter_type": "ml_infra",
        "config": {
            "base_url": "http://localhost:8000",
            "auth_token": "test-token",
        },
    }
