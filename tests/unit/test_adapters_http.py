"""Tests for HTTPAdapter."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from aieval.adapters.http import HTTPAdapter


class TestHTTPAdapter:
    """Tests for HTTPAdapter."""
    
    def test_init_defaults(self):
        """Test HTTPAdapter initialization with defaults."""
        adapter = HTTPAdapter()
        
        assert adapter.base_url == "http://localhost:8000"
        assert adapter.context_field_name == "context"
        assert adapter.default_endpoint == "/chat/platform"
        assert adapter.response_format == "json"
    
    def test_init_custom_config(self):
        """Test HTTPAdapter initialization with custom config."""
        adapter = HTTPAdapter(
            base_url="https://api.example.com",
            auth_token="test-token",
            context_field_name="harness_context",
            context_data={"account_id": "acc-123"},
            endpoint_mapping={"pipeline": "/custom/pipeline"},
            default_endpoint="/custom/default",
            response_format="sse",
        )
        
        assert adapter.base_url == "https://api.example.com"
        assert adapter.context_field_name == "harness_context"
        assert adapter.context_data["account_id"] == "acc-123"
        assert adapter.endpoint_mapping["pipeline"] == "/custom/pipeline"
        assert adapter.default_endpoint == "/custom/default"
        assert adapter.response_format == "sse"
        assert "Bearer test-token" in adapter.headers["Authorization"]
    
    def test_get_endpoint_with_mapping(self):
        """Test endpoint selection with entity type mapping."""
        adapter = HTTPAdapter(
            endpoint_mapping={"pipeline": "/custom/pipeline"}
        )
        
        endpoint = adapter._get_endpoint("pipeline")
        assert endpoint == "http://localhost:8000/custom/pipeline"
    
    def test_get_endpoint_default(self):
        """Test endpoint selection with default."""
        adapter = HTTPAdapter()
        
        endpoint = adapter._get_endpoint("unknown_entity")
        assert endpoint == "http://localhost:8000/chat/platform"
    
    def test_determine_provider_claude(self):
        """Test provider detection for Claude models."""
        adapter = HTTPAdapter()
        
        assert adapter._determine_provider("claude-3-5-sonnet") == "anthropic"
        assert adapter._determine_provider("claude-3-opus") == "anthropic"
    
    def test_determine_provider_openai(self):
        """Test provider detection for OpenAI models."""
        adapter = HTTPAdapter()
        
        assert adapter._determine_provider("gpt-4o") == "openai"
        assert adapter._determine_provider("gpt-3.5-turbo") == "openai"
        assert adapter._determine_provider("o1-preview") == "openai"
    
    def test_determine_provider_default(self):
        """Test provider detection defaults to OpenAI."""
        adapter = HTTPAdapter()
        
        assert adapter._determine_provider(None) == "openai"
        assert adapter._determine_provider("unknown-model") == "openai"
    
    @pytest.mark.asyncio
    async def test_generate_json_response(self):
        """Test generating output with JSON response."""
        adapter = HTTPAdapter(
            base_url="http://test-server",
            yaml_extraction_path=["result", "yaml"]
        )
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value={
            "result": {"yaml": "key: value"}
        })
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test", "entity_type": "pipeline"},
                model="gpt-4o"
            )
            
            assert result == "key: value"
    
    @pytest.mark.asyncio
    async def test_generate_sse_response(self):
        """Test generating output with SSE response."""
        adapter = HTTPAdapter(
            base_url="http://test-server",
            response_format="sse",
            sse_completion_events=["complete"]
        )
        
        # Mock SSE response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/event-stream"}
        mock_response.content = AsyncMock()
        
        # Mock SSE stream
        async def mock_iter():
            yield b"data: {\"event\": \"complete\", \"yaml\": \"key: value\"}\n\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test", "entity_type": "pipeline"},
                model="gpt-4o"
            )
            
            # Should extract YAML from SSE
            assert "key: value" in result or result == "key: value"
    
    @pytest.mark.asyncio
    async def test_generate_error_response(self):
        """Test handling error responses."""
        adapter = HTTPAdapter(base_url="http://test-server")
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception):
                await adapter.generate(
                    {"prompt": "test", "entity_type": "pipeline"},
                    model="gpt-4o"
                )
    
    def test_generate_payload_with_context(self):
        """Test payload generation with context."""
        adapter = HTTPAdapter(
            context_field_name="harness_context",
            context_data={"account_id": "acc-123", "org_id": "org-456"}
        )
        
        payload = adapter._generate_payload(
            prompt="Create pipeline",
            entity_type="pipeline",
            operation_type="create"
        )
        
        assert payload["harness_context"]["account_id"] == "acc-123"
        assert payload["harness_context"]["org_id"] == "org-456"
        assert payload["prompt"] == "Create pipeline"
    
    def test_generate_payload_with_old_yaml(self):
        """Test payload generation with old YAML for updates."""
        adapter = HTTPAdapter()
        
        payload = adapter._generate_payload(
            prompt="Update pipeline",
            entity_type="pipeline",
            operation_type="update",
            old_yaml="key: old_value"
        )
        
        assert "old_yaml" in payload or "oldYaml" in payload or payload.get("yaml") == "key: old_value"
