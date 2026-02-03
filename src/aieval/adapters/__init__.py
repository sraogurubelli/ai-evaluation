"""Adapters for different AI systems.

Teams should create their own custom adapters rather than adding
team-specific adapters to the core codebase.

See docs/custom-adapters.md for guidance on creating custom adapters.
"""

from aieval.adapters.base import Adapter
from aieval.adapters.http import HTTPAdapter
from aieval.adapters.langfuse import LangfuseAdapter
from aieval.adapters.sse_streaming import SSEStreamingAdapter
from aieval.adapters.registry import (
    AdapterRegistry,
    register_adapter,
    get_registry,
)

__all__ = [
    "Adapter",  # Base interface
    "HTTPAdapter",  # Generic HTTP adapter (recommended)
    "LangfuseAdapter",  # Langfuse integration
    "SSEStreamingAdapter",  # SSE streaming adapter with enriched output
    "AdapterRegistry",  # Adapter registry for plugin system
    "register_adapter",  # Decorator for registering adapters
    "get_registry",  # Get default registry instance
]

# Note: MLInfraAdapter has been removed.
# Teams should create their own adapters using HTTPAdapter or by
# implementing the Adapter interface. See docs/custom-adapters.md

# Initialize default registry with built-in adapters
from aieval.adapters.factory import register_builtin_adapters
register_builtin_adapters(get_registry())
