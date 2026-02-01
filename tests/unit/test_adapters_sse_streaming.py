"""Tests for SSEStreamingAdapter."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from ai_evolution.adapters.sse_streaming import SSEStreamingAdapter


class TestSSEStreamingAdapter:
    """Tests for SSEStreamingAdapter."""
    
    def test_init_defaults(self):
        """Test SSEStreamingAdapter initialization with defaults."""
        adapter = SSEStreamingAdapter()
        
        assert adapter.base_url == "http://localhost:8000"
        assert adapter.endpoint == "/chat/stream"
        assert "complete" in adapter.completion_events
        assert "tool_call" in adapter.tool_call_events
        assert adapter.usage_event == "usage"
    
    def test_init_custom_config(self):
        """Test SSEStreamingAdapter initialization with custom config."""
        adapter = SSEStreamingAdapter(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer test-token"},
            context_data={"account_id": "acc-123"},
            endpoint="/custom/stream",
            completion_events=["custom_complete"],
            tool_call_events=["custom_tool"],
            usage_event="custom_usage",
        )
        
        assert adapter.base_url == "https://api.example.com"
        assert adapter.endpoint == "/custom/stream"
        assert adapter.completion_events == ["custom_complete"]
        assert adapter.tool_call_events == ["custom_tool"]
        assert adapter.usage_event == "custom_usage"
        assert "Bearer test-token" in adapter.headers["Authorization"]
    
    def test_generate_payload(self):
        """Test payload generation."""
        adapter = SSEStreamingAdapter(
            context_data={"account_id": "acc-123"}
        )
        
        payload = adapter._generate_payload(
            {"prompt": "Create pipeline", "entity_type": "pipeline"},
            model="gpt-4o"
        )
        
        assert payload["prompt"] == "Create pipeline"
        assert payload["stream"] is True
        assert payload["model"] == "gpt-4o"
        assert payload["entity_type"] == "pipeline"
        assert payload["context"]["account_id"] == "acc-123"
    
    def test_generate_payload_with_old_yaml(self):
        """Test payload generation with old YAML."""
        adapter = SSEStreamingAdapter()
        
        payload = adapter._generate_payload(
            {
                "prompt": "Update pipeline",
                "entity_type": "pipeline",
                "operation_type": "update",
                "old_yaml": "key: old_value"
            }
        )
        
        assert payload["old_yaml"] == "key: old_value"
        assert payload["operation_type"] == "update"
    
    @pytest.mark.asyncio
    async def test_generate_sse_stream_success(self):
        """Test successful SSE stream parsing."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        # Mock SSE response
        mock_response = AsyncMock()
        mock_response.status = 200
        
        # Mock SSE stream with multiple events
        async def mock_iter():
            # Event 1: Tool call
            yield b"event: tool_call\n"
            yield b'data: {"tool_name": "search", "parameters": {"query": "test"}}\n'
            yield b"\n"
            # Event 2: Completion with YAML
            yield b"event: complete\n"
            yield b'data: {"yaml": "pipeline:\\n  name: test"}\n'
            yield b"\n"
            # Event 3: Usage info
            yield b"event: usage\n"
            yield b'data: {"total_tokens": 500, "prompt_tokens": 100, "completion_tokens": 400}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test", "entity_type": "pipeline"},
                model="gpt-4o"
            )
            
            # Parse enriched output
            output = json.loads(result)
            
            # Verify structure
            assert "final_yaml" in output
            assert "events" in output
            assert "tools_called" in output
            assert "metrics" in output
            
            # Verify final YAML
            assert output["final_yaml"] == "pipeline:\n  name: test"
            
            # Verify events collected
            assert len(output["events"]) == 3
            assert output["events"][0]["event"] == "tool_call"
            assert output["events"][1]["event"] == "complete"
            assert output["events"][2]["event"] == "usage"
            
            # Verify tool extraction
            assert len(output["tools_called"]) == 1
            assert output["tools_called"][0]["tool"] == "search"
            assert output["tools_called"][0]["parameters"]["query"] == "test"
            
            # Verify metrics
            assert output["metrics"]["latency_ms"] >= 0
            assert output["metrics"]["total_events"] == 3
            assert output["metrics"]["total_tokens"] == 500
            assert output["metrics"]["prompt_tokens"] == 100
            assert output["metrics"]["completion_tokens"] == 400
    
    @pytest.mark.asyncio
    async def test_generate_multiple_tools(self):
        """Test extraction of multiple tool calls."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        async def mock_iter():
            yield b"event: tool_call\n"
            yield b'data: {"tool_name": "search", "parameters": {"q": "test1"}}\n'
            yield b"\n"
            yield b"event: tool_call\n"
            yield b'data: {"tool_name": "calculate", "parameters": {"expr": "2+2"}}\n'
            yield b"\n"
            yield b"event: complete\n"
            yield b'data: {"yaml": "result"}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test"},
                model="gpt-4o"
            )
            
            output = json.loads(result)
            
            # Verify multiple tools extracted
            assert len(output["tools_called"]) == 2
            assert output["tools_called"][0]["tool"] == "search"
            assert output["tools_called"][1]["tool"] == "calculate"
    
    @pytest.mark.asyncio
    async def test_generate_no_completion_event(self):
        """Test handling when no completion event received."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        async def mock_iter():
            yield b"event: partial\n"
            yield b'data: {"partial": "output"}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test"},
                model="gpt-4o"
            )
            
            output = json.loads(result)
            
            # Verify empty final_yaml when no completion event
            assert output["final_yaml"] == ""
            assert len(output["events"]) == 1
    
    @pytest.mark.asyncio
    async def test_generate_error_response(self):
        """Test handling of error responses."""
        adapter = SSEStreamingAdapter(base_url="http://test-server")
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(RuntimeError) as exc_info:
                await adapter.generate(
                    {"prompt": "test"},
                    model="gpt-4o"
                )
            
            assert "API error 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_malformed_json(self):
        """Test handling of malformed JSON in SSE data."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        async def mock_iter():
            # Malformed JSON (should be skipped)
            yield b"event: bad\n"
            yield b"data: {invalid json}\n"
            yield b"\n"
            # Valid event
            yield b"event: complete\n"
            yield b'data: {"yaml": "valid"}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test"},
                model="gpt-4o"
            )
            
            output = json.loads(result)
            
            # Should skip malformed event and process valid one
            assert output["final_yaml"] == "valid"
            assert len(output["events"]) == 1  # Only valid event
    
    @pytest.mark.asyncio
    async def test_generate_alternative_yaml_fields(self):
        """Test extraction of YAML from alternative field names."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        async def mock_iter():
            yield b"event: complete\n"
            yield b'data: {"output": "alternative_field"}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test"},
                model="gpt-4o"
            )
            
            output = json.loads(result)
            
            # Should extract from "output" field
            assert output["final_yaml"] == "alternative_field"
    
    @pytest.mark.asyncio
    async def test_generate_timestamps(self):
        """Test that timestamps are properly tracked."""
        adapter = SSEStreamingAdapter(
            base_url="http://test-server",
            completion_events=["complete"],
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        async def mock_iter():
            yield b"event: event1\n"
            yield b'data: {"data": "first"}\n'
            yield b"\n"
            yield b"event: event2\n"
            yield b'data: {"data": "second"}\n'
            yield b"\n"
        
        mock_response.content.__aiter__ = mock_iter
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await adapter.generate(
                {"prompt": "test"},
                model="gpt-4o"
            )
            
            output = json.loads(result)
            
            # Verify timestamps exist and are ordered
            assert len(output["events"]) == 2
            assert "timestamp" in output["events"][0]
            assert "timestamp" in output["events"][1]
            assert output["events"][0]["timestamp"] >= 0
            assert output["events"][1]["timestamp"] >= output["events"][0]["timestamp"]


class TestSSEStreamingAdapterEnhancements:
    """Tests for enhanced SSEStreamingAdapter features."""
    
    def test_custom_headers(self):
        """Test custom headers configuration."""
        adapter = SSEStreamingAdapter(
            headers={
                "Authorization": "Bearer my-token",
                "X-API-Key": "custom-key",
                "X-Request-ID": "req-123",
            }
        )
        
        assert adapter.headers["Authorization"] == "Bearer my-token"
        assert adapter.headers["X-API-Key"] == "custom-key"
        assert adapter.headers["X-Request-ID"] == "req-123"
        assert adapter.headers["Content-Type"] == "application/json"
    
    def test_headers_override_defaults(self):
        """Test that custom headers override defaults."""
        adapter = SSEStreamingAdapter(
            headers={"Content-Type": "text/plain"}
        )
        
        assert adapter.headers["Content-Type"] == "text/plain"
    
    def test_custom_payload_builder(self):
        """Test custom payload builder function."""
        def my_builder(input_data, model):
            return {
                "query": input_data.get("prompt"),
                "llm_model": model,
                "custom_field": "value"
            }
        
        adapter = SSEStreamingAdapter(payload_builder=my_builder)
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert payload["query"] == "test"
        assert payload["llm_model"] == "gpt-4o"
        assert payload["custom_field"] == "value"
    
    def test_payload_template_with_uuids(self):
        """Test payload template with UUID generation."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "request_id": "__uuid__",
                "prompt": "__input__.prompt",
                "model": "__model__",
                "static_field": "static_value"
            }
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert len(payload["request_id"]) == 36  # UUID length
        assert payload["prompt"] == "test"
        assert payload["model"] == "gpt-4o"
        assert payload["static_field"] == "static_value"
    
    def test_payload_template_with_timestamp(self):
        """Test payload template with timestamp generation."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "ts": "__timestamp__",
                "data": "test"
            }
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert isinstance(payload["ts"], int)
        assert payload["ts"] > 0
        assert payload["data"] == "test"
    
    def test_payload_template_nested(self):
        """Test payload template with nested structures."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "id": "__uuid__",
                "metadata": {
                    "prompt": "__input__.prompt",
                    "model": "__model__",
                    "static": "value"
                }
            }
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert len(payload["id"]) == 36
        assert payload["metadata"]["prompt"] == "test"
        assert payload["metadata"]["model"] == "gpt-4o"
        assert payload["metadata"]["static"] == "value"
    
    def test_payload_template_with_list(self):
        """Test payload template with list containing dicts."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "messages": [
                    {"role": "user", "content": "__input__.prompt"}
                ],
                "model": "__model__"
            }
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "test"
        assert payload["model"] == "gpt-4o"
    
    def test_include_uuids(self):
        """Test include_uuids parameter adds conversation_id and interaction_id."""
        adapter = SSEStreamingAdapter(include_uuids=True)
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert "conversation_id" in payload
        assert "interaction_id" in payload
        assert len(payload["conversation_id"]) == 36
        assert len(payload["interaction_id"]) == 36
        assert payload["conversation_id"] != payload["interaction_id"]
    
    def test_httpAdapter_compatibility(self):
        """Test HTTPAdapter-style payload building."""
        adapter = SSEStreamingAdapter(
            include_uuids=True,
            context_data={"account_id": "acc-123", "org_id": "org-456"}
        )
        
        payload = adapter._generate_payload(
            {"prompt": "Create pipeline", "entity_type": "pipeline"},
            "gpt-4o"
        )
        
        assert "conversation_id" in payload
        assert "interaction_id" in payload
        assert len(payload["conversation_id"]) == 36
        assert payload["context"]["account_id"] == "acc-123"
        assert payload["context"]["org_id"] == "org-456"
        assert payload["prompt"] == "Create pipeline"
        assert payload["entity_type"] == "pipeline"
        assert payload["model"] == "gpt-4o"
    
    def test_payload_template_overrides_default(self):
        """Test that payload_template overrides default payload building."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "custom_prompt": "__input__.prompt",
                "custom_model": "__model__"
            }
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        # Should not have default fields
        assert "prompt" not in payload
        assert "stream" not in payload
        # Should have template fields
        assert payload["custom_prompt"] == "test"
        assert payload["custom_model"] == "gpt-4o"
    
    def test_payload_builder_overrides_template(self):
        """Test that payload_builder takes precedence over template."""
        def my_builder(input_data, model):
            return {"builder": "used"}
        
        adapter = SSEStreamingAdapter(
            payload_builder=my_builder,
            payload_template={"template": "ignored"}
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        assert payload == {"builder": "used"}
        assert "template" not in payload
    
    def test_combine_template_and_uuids(self):
        """Test combining payload_template with include_uuids."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "query": "__input__.prompt",
                "model": "__model__"
            },
            include_uuids=True
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        # Should have template fields
        assert payload["query"] == "test"
        assert payload["model"] == "gpt-4o"
        # Should also have UUIDs
        assert "conversation_id" in payload
        assert "interaction_id" in payload
    
    def test_combine_template_and_context(self):
        """Test combining payload_template with context_data."""
        adapter = SSEStreamingAdapter(
            payload_template={
                "prompt": "__input__.prompt"
            },
            context_data={"account_id": "acc-123"}
        )
        
        payload = adapter._generate_payload({"prompt": "test"}, "gpt-4o")
        
        # Should have template fields
        assert payload["prompt"] == "test"
        # Should also have context
        assert payload["context"]["account_id"] == "acc-123"
    
    def test_backward_compatibility_default_payload(self):
        """Test that default behavior still works without new params."""
        adapter = SSEStreamingAdapter(
            context_data={"account_id": "acc-123"}
        )
        
        payload = adapter._generate_payload(
            {"prompt": "test", "entity_type": "pipeline"},
            "gpt-4o"
        )
        
        # Should have default fields
        assert payload["prompt"] == "test"
        assert payload["stream"] is True
        assert payload["model"] == "gpt-4o"
        assert payload["entity_type"] == "pipeline"
        assert payload["context"]["account_id"] == "acc-123"
