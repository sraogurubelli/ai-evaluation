"""Tests for MLInfraAdapter."""

import pytest
from unittest.mock import AsyncMock, patch
from ai_evolution.adapters.ml_infra import MLInfraAdapter


class TestMLInfraAdapter:
    """Tests for MLInfraAdapter."""
    
    def test_init_defaults(self):
        """Test MLInfraAdapter initialization with defaults."""
        adapter = MLInfraAdapter()
        
        assert adapter.context_field_name == "harness_context"
        assert adapter.context_data["account_id"] == "default"
        assert adapter.context_data["org_id"] == "default"
        assert adapter.context_data["project_id"] == "default"
    
    def test_init_custom_config(self):
        """Test MLInfraAdapter initialization with custom config."""
        adapter = MLInfraAdapter(
            base_url="https://ml-infra.example.com",
            auth_token="test-token",
            account_id="acc-123",
            org_id="org-456",
            project_id="proj-789"
        )
        
        assert adapter.base_url == "https://ml-infra.example.com"
        assert adapter.context_data["account_id"] == "acc-123"
        assert adapter.context_data["org_id"] == "org-456"
        assert adapter.context_data["project_id"] == "proj-789"
    
    def test_get_endpoint_pipeline(self):
        """Test endpoint selection for pipeline."""
        adapter = MLInfraAdapter()
        
        endpoint = adapter._get_endpoint("pipeline")
        assert endpoint == "http://localhost:8000/chat/platform"
    
    def test_get_endpoint_dashboard(self):
        """Test endpoint selection for dashboard."""
        adapter = MLInfraAdapter()
        
        endpoint = adapter._get_endpoint("dashboard")
        assert endpoint == "http://localhost:8000/chat/dashboard"
    
    def test_get_endpoint_knowledge_graph(self):
        """Test endpoint selection for knowledge graph."""
        adapter = MLInfraAdapter()
        
        endpoint = adapter._get_endpoint("knowledge_graph")
        assert endpoint == "http://localhost:8000/chat/knowledge-graph"
    
    def test_inherits_from_http_adapter(self):
        """Test that MLInfraAdapter inherits from HTTPAdapter."""
        adapter = MLInfraAdapter()
        
        # Should have HTTPAdapter methods
        assert hasattr(adapter, "_generate_payload")
        assert hasattr(adapter, "_determine_provider")
        assert hasattr(adapter, "generate")
