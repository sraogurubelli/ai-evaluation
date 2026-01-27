"""Tests for Task abstraction."""

import pytest
from unittest.mock import AsyncMock
from ai_evolution.sdk.task import FunctionTask, AdapterTask
from tests.fixtures.mock_adapter import MockAdapter


class TestFunctionTask:
    """Tests for FunctionTask."""
    
    @pytest.mark.asyncio
    async def test_function_task(self):
        """Test FunctionTask with async function."""
        async def my_func(input_data):
            return f"Output: {input_data.get('prompt', '')}"
        
        task = FunctionTask(my_func)
        result = await task.run({"prompt": "test"})
        
        assert result == "Output: test"
    
    @pytest.mark.asyncio
    async def test_function_task_with_complex_input(self):
        """Test FunctionTask with complex input."""
        async def my_func(input_data):
            return {
                "output": input_data.get("prompt"),
                "metadata": input_data.get("metadata", {}),
            }
        
        task = FunctionTask(my_func)
        result = await task.run({
            "prompt": "test",
            "metadata": {"entity_type": "pipeline"},
        })
        
        assert result["output"] == "test"
        assert result["metadata"]["entity_type"] == "pipeline"


class TestAdapterTask:
    """Tests for AdapterTask."""
    
    @pytest.mark.asyncio
    async def test_adapter_task(self):
        """Test AdapterTask wrapper."""
        adapter = MockAdapter()
        task = AdapterTask(adapter, model="gpt-4o")
        
        result = await task.run({"prompt": "test", "entity_type": "pipeline"})
        
        assert result is not None
        assert adapter.call_count == 1
    
    @pytest.mark.asyncio
    async def test_adapter_task_with_model(self):
        """Test AdapterTask with model parameter."""
        adapter = MockAdapter()
        task = AdapterTask(adapter, model="claude-3-5-sonnet")
        
        result = await task.run({"prompt": "test"})
        
        assert result is not None
