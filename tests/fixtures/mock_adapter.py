"""Mock adapter fixtures for testing."""

from unittest.mock import AsyncMock
from aieval.adapters.base import Adapter


class MockAdapter(Adapter):
    """Mock adapter for testing."""

    def __init__(self, responses=None):
        """Initialize mock adapter with optional responses."""
        super().__init__()
        self.responses = responses or {}
        self.call_count = 0

    async def generate(self, input_data, model=None, **kwargs):
        """Generate mock output."""
        self.call_count += 1
        key = input_data.get("prompt", "default")
        return self.responses.get(key, f"Mock output for: {key}")
