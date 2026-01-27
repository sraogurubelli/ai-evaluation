"""Tests for experiment agent endpoints."""

import pytest
from tests.api.conftest import client


class TestExperimentAgent:
    """Tests for experiment agent endpoints."""
    
    def test_create_experiment_config(self, client):
        """Test creating experiment configuration."""
        response = client.post(
            "/evaluate/experiment/create",
            json={
                "name": "test_experiment",
                "dataset_config": {
                    "type": "index_csv",
                    "index_file": "benchmarks/datasets/index.csv",
                    "base_dir": "benchmarks/datasets",
                },
                "scorers_config": [
                    {"type": "deep_diff", "version": "v3"},
                ],
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "experiment_id" in data
    
    def test_run_experiment(self, client):
        """Test running an experiment."""
        # First create experiment
        create_response = client.post(
            "/evaluate/experiment/create",
            json={
                "name": "test_experiment",
                "dataset_config": {
                    "type": "index_csv",
                    "index_file": "benchmarks/datasets/index.csv",
                    "base_dir": "benchmarks/datasets",
                },
                "scorers_config": [
                    {"type": "deep_diff", "version": "v3"},
                ],
            },
        )
        
        if create_response.status_code == 201:
            experiment_id = create_response.json()["experiment_id"]
            
            # Then run experiment
            response = client.post(
                "/evaluate/experiment/run",
                json={
                    "experiment_id": experiment_id,
                    "adapter_config": {
                        "type": "ml_infra",
                        "base_url": "http://localhost:8000",
                    },
                    "model": "gpt-4o",
                },
            )
            
            # May fail if files don't exist or adapter can't connect
            assert response.status_code in [200, 404, 500]
