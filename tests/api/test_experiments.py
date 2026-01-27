"""Tests for experiment endpoints."""

import pytest
from tests.api.conftest import client


class TestExperimentsEndpoint:
    """Tests for /experiments endpoint."""
    
    def test_create_experiment_success(self, client, sample_dataset_config, sample_adapter_config):
        """Test successful experiment creation."""
        response = client.post(
            "/experiments",
            json={
                "experiment_name": "test_experiment",
                "config": {
                    "dataset": sample_dataset_config,
                    "adapter": sample_adapter_config,
                    "scorers": [{"type": "deep_diff", "version": "v3"}],
                    "models": ["gpt-4o"],
                },
                "run_async": True,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["experiment_name"] == "test_experiment"
        assert data["status"] == "pending"
    
    def test_create_experiment_invalid_config(self, client):
        """Test experiment creation with invalid config."""
        response = client.post(
            "/experiments",
            json={
                "experiment_name": "test",
                "config": {},  # Invalid config
                "run_async": True,
            },
        )
        
        # Should return error
        assert response.status_code in [400, 422, 500]
    
    def test_create_experiment_missing_fields(self, client):
        """Test experiment creation with missing required fields."""
        response = client.post(
            "/experiments",
            json={
                "experiment_name": "test",
                # Missing config
            },
        )
        
        assert response.status_code == 422  # Validation error
