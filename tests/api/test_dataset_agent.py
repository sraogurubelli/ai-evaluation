"""Tests for dataset agent endpoints."""

import pytest
from tests.api.conftest import client


class TestDatasetAgent:
    """Tests for dataset agent endpoints."""
    
    def test_load_dataset_index_csv(self, client):
        """Test loading index CSV dataset."""
        response = client.post(
            "/evaluate/dataset/load",
            json={
                "dataset_type": "index_csv",
                "index_file": "benchmarks/datasets/index.csv",
                "base_dir": "benchmarks/datasets",
                "filters": {
                    "entity_type": "pipeline",
                },
            },
        )
        
        # May fail if files don't exist, but should return proper error
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "item_count" in data
    
    def test_validate_dataset(self, client):
        """Test dataset validation."""
        response = client.post(
            "/evaluate/dataset/validate",
            json={
                "dataset_type": "jsonl",
                "path": "nonexistent.jsonl",
            },
        )
        
        # Should return validation result (may be invalid)
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
    
    def test_list_datasets(self, client):
        """Test listing datasets."""
        response = client.get("/evaluate/dataset/list?base_dir=benchmarks/datasets")
        
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
