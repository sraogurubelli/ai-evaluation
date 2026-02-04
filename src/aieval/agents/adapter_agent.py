"""Adapter agent for AI system integration."""

import os
from typing import Any

from aieval.agents.base import BaseEvaluationAgent
from aieval.adapters.base import Adapter
from aieval.adapters.registry import get_registry


class AdapterAgent(BaseEvaluationAgent):
    """Agent for AI system integration (ML Infra, Langfuse, etc.)."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize adapter agent."""
        super().__init__(config)
        self._adapters: dict[str, Adapter] = {}
        self._registry = get_registry()
        # Discover entry points on initialization
        self._registry.discover_entry_points()
    
    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run adapter operation based on query.
        
        Supported queries:
        - "create": Create an adapter
        - "generate": Generate output using adapter
        - "list": List available adapters
        
        Args:
            query: Operation to perform
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        if query == "create":
            return await self.create_adapter(**kwargs)
        elif query == "generate":
            return await self.generate(**kwargs)
        elif query == "list":
            return await self.list_adapters(**kwargs)
        else:
            raise ValueError(f"Unknown query: {query}")
    
    async def create_adapter(
        self,
        adapter_type: str,
        name: str | None = None,
        **kwargs: Any,
    ) -> Adapter:
        """
        Create an adapter using the registry system.
        
        Args:
            adapter_type: Type of adapter (e.g., "http", "sse_streaming", "langfuse", or custom)
            name: Optional name for the adapter (for caching)
            **kwargs: Adapter-specific configuration
            
        Returns:
            Created adapter instance
            
        Raises:
            ValueError: If adapter type is not registered
        """
        self.logger.info(f"Creating adapter of type: {adapter_type}")
        
        adapter_id = name or f"{adapter_type}_{id(kwargs)}"
        
        # Check cache
        if adapter_id in self._adapters:
            self.logger.info(f"Returning cached adapter: {adapter_id}")
            return self._adapters[adapter_id]
        
        # Create adapter using registry
        try:
            adapter = self._registry.create(adapter_type, **kwargs)
        except ValueError as e:
            self.logger.error(f"Failed to create adapter {adapter_type}: {e}")
            raise
        
        # Cache adapter
        self._adapters[adapter_id] = adapter
        
        self.logger.info(f"Created adapter: {adapter_type}")
        return adapter
    
    def register_adapter(
        self,
        adapter_type: str,
        module_path: str,
        class_name: str,
        factory_kwargs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a custom adapter dynamically.
        
        Args:
            adapter_type: Unique identifier for the adapter type
            module_path: Python module path (e.g., "my_team.adapters")
            class_name: Class name of the adapter
            factory_kwargs: Optional default kwargs to pass to adapter constructor
            metadata: Optional metadata about the adapter
        """
        self._registry.register_from_module(
            adapter_type=adapter_type,
            module_path=module_path,
            class_name=class_name,
            factory_kwargs=factory_kwargs,
            metadata=metadata,
        )
        self.logger.info(f"Registered custom adapter: {adapter_type} from {module_path}.{class_name}")
    
    async def generate(
        self,
        adapter: Adapter | str,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate output using adapter.
        
        Args:
            adapter: Adapter instance or adapter ID (if cached)
            input_data: Input data for generation
            model: Optional model name
            **kwargs: Additional parameters
            
        Returns:
            Generated output
        """
        # Resolve adapter if ID provided
        if isinstance(adapter, str):
            if adapter not in self._adapters:
                raise ValueError(f"Adapter {adapter} not found. Create it first.")
            adapter = self._adapters[adapter]
        
        self.logger.info(f"Generating output with adapter {type(adapter).__name__}")
        
        output = await adapter.generate(
            input_data,
            model=model,
            **kwargs,
        )
        
        self.logger.info("Output generated successfully")
        return output
    
    async def list_adapters(self, **kwargs: Any) -> dict[str, Any]:
        """
        List available adapters.
        
        Returns:
            Dictionary with cached adapters and available adapter types
        """
        adapters = []
        
        # List cached adapters
        for adapter_id, adapter in self._adapters.items():
            metadata = adapter.get_metadata()
            adapters.append({
                "id": adapter_id,
                "type": type(adapter).__name__,
                "metadata": metadata,
            })
        
        # List available adapter types from registry
        available_types = self._registry.list_types()
        
        return {
            "cached": adapters,
            "available_types": available_types,
        }
