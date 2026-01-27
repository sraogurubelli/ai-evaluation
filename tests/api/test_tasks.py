"""Tests for task endpoints."""

import pytest
from tests.api.conftest import client


class TestTasksEndpoint:
    """Tests for /tasks endpoints."""
    
    def test_list_tasks(self, client):
        """Test listing tasks."""
        response = client.get("/tasks")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_tasks_with_status_filter(self, client):
        """Test listing tasks with status filter."""
        response = client.get("/tasks?status=completed")
        
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
    
    def test_list_tasks_with_limit(self, client):
        """Test listing tasks with limit."""
        response = client.get("/tasks?limit=10")
        
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) <= 10
    
    def test_get_task_by_id_not_found(self, client):
        """Test getting non-existent task."""
        response = client.get("/tasks/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_task_result_not_found(self, client):
        """Test getting result for non-existent task."""
        response = client.get("/tasks/nonexistent-id/result")
        
        assert response.status_code == 404
