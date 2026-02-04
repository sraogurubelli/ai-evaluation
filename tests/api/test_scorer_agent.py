"""Tests for scorer agent endpoints."""

import pytest


class TestScorerAgent:
    """Tests for scorer agent endpoints."""
    
    def test_create_scorer(self, client):
        """Test creating a scorer."""
        response = client.post(
            "/evaluate/scorer/create",
            json={
                "scorer_type": "deep_diff",
                "name": "test_scorer",
                "config": {
                    "version": "v3",
                },
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "scorer_id" in data
    
    def test_score_item(self, client):
        """Test scoring an item."""
        # First create scorer
        create_response = client.post(
            "/evaluate/scorer/create",
            json={
                "scorer_type": "deep_diff",
                "name": "test_scorer",
                "config": {"version": "v3"},
            },
        )
        
        if create_response.status_code == 201:
            scorer_id = create_response.json()["scorer_id"]
            
            # Then score an item
            response = client.post(
                "/evaluate/scorer/score",
                json={
                    "scorer_id": scorer_id,
                    "item": {
                        "id": "test-001",
                        "input": {"prompt": "test"},
                        "expected": {"yaml": "key: value"},
                    },
                    "output": "key: value",
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "score" in data
    
    def test_list_scorers(self, client):
        """Test listing scorers."""
        response = client.get("/evaluate/scorer/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "cached" in data
        assert "available_types" in data
