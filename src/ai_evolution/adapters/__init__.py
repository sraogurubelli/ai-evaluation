"""Adapters for different AI systems.

Teams should create their own custom adapters rather than adding
team-specific adapters to the core codebase.

See docs/custom-adapters.md for guidance on creating custom adapters.
"""

from ai_evolution.adapters.base import Adapter
from ai_evolution.adapters.http import HTTPAdapter
from ai_evolution.adapters.langfuse import LangfuseAdapter

__all__ = [
    "Adapter",  # Base interface
    "HTTPAdapter",  # Generic HTTP adapter (recommended)
    "LangfuseAdapter",  # Langfuse integration
]

# Note: MLInfraAdapter has been removed.
# Teams should create their own adapters using HTTPAdapter or by
# implementing the Adapter interface. See docs/custom-adapters.md
