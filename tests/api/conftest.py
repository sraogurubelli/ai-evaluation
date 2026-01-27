"""Fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient
from ai_evolution.api.app import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


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
