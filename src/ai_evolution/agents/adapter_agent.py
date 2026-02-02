"""Adapter agent for AI system integration."""

import os
from typing import Any

from ai_evolution.agents.base import BaseEvaluationAgent
from ai_evolution.adapters.base import Adapter
from ai_evolution.adapters.http import HTTPAdapter
from ai_evolution.adapters.langfuse import LangfuseAdapter
from ai_evolution.adapters.sse_streaming import SSEStreamingAdapter


class AdapterAgent(BaseEvaluationAgent):
    """Agent for AI system integration (ML Infra, Langfuse, etc.)."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize adapter agent."""
        super().__init__(config)
        self._adapters: dict[str, Adapter] = {}
    
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
        Create an adapter.
        
        Args:
            adapter_type: Type of adapter ("http", "langfuse"). Note: "ml_infra" is deprecated, use "http" with ml-infra config.
            name: Optional name for the adapter (for caching)
            **kwargs: Adapter-specific configuration
            
        Returns:
            Created adapter instance
        """
        self.logger.info(f"Creating adapter of type: {adapter_type}")
        
        adapter_id = name or f"{adapter_type}_{id(kwargs)}"
        
        # Check cache
        if adapter_id in self._adapters:
            self.logger.info(f"Returning cached adapter: {adapter_id}")
            return self._adapters[adapter_id]
        
        adapter: Adapter
        
        if adapter_type == "http" or adapter_type == "rest":
            # Generic HTTP adapter (recommended)
            base_url = kwargs.get("base_url") or os.getenv("CHAT_BASE_URL", "http://localhost:8000")
            auth_token = kwargs.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")
            
            adapter = HTTPAdapter(
                base_url=base_url,
                auth_token=auth_token,
                context_field_name=kwargs.get("context_field_name", "context"),
                context_data=kwargs.get("context_data", {}),
                endpoint_mapping=kwargs.get("endpoint_mapping", {}),
                default_endpoint=kwargs.get("default_endpoint", "/chat/platform"),
                response_format=kwargs.get("response_format", "json"),
                yaml_extraction_path=kwargs.get("yaml_extraction_path"),
                sse_completion_events=kwargs.get("sse_completion_events"),
            )
        
        elif adapter_type == "ml_infra":
            # Deprecated: Use "http" adapter type with ml-infra configuration instead
            # This is kept for backward compatibility but will be removed in future versions
            import warnings
            warnings.warn(
                "ml_infra adapter type is deprecated. Use 'http' adapter type with ml-infra "
                "configuration instead. See docs/custom-adapters.md for migration guide.",
                DeprecationWarning,
                stacklevel=2
            )
            
            base_url = kwargs.get("base_url") or os.getenv("CHAT_BASE_URL", "http://localhost:8000")
            auth_token = kwargs.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")
            account_id = kwargs.get("account_id") or os.getenv("ACCOUNT_ID", "default")
            org_id = kwargs.get("org_id") or os.getenv("ORG_ID", "default")
            project_id = kwargs.get("project_id") or os.getenv("PROJECT_ID", "default")
            
            # Check if SSE streaming with enriched output is requested
            use_sse_streaming = kwargs.get("use_sse_streaming", False)
            
            if use_sse_streaming:
                # Use SSEStreamingAdapter for enriched output (events, tools, metrics)
                adapter = SSEStreamingAdapter(
                    base_url=base_url,
                    headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
                    context_data={
                        "account_id": account_id,
                        "org_id": org_id,
                        "project_id": project_id,
                    },
                    endpoint="/chat/stream",  # Default SSE endpoint
                    completion_events=[
                        "complete",
                        "dashboard_complete",
                        "kg_complete",
                    ],
                    tool_call_events=[
                        "tool_call",
                        "function_call",
                    ],
                    include_uuids=True,  # HTTPAdapter compatibility
                )
            else:
                # Use HTTPAdapter with ml-infra configuration (backward compatible)
                adapter = HTTPAdapter(
                    base_url=base_url,
                    auth_token=auth_token,
                    context_field_name="harness_context",
                    context_data={
                        "account_id": account_id,
                        "org_id": org_id,
                        "project_id": project_id,
                    },
                    endpoint_mapping={
                        "dashboard": "/chat/dashboard",
                        "knowledge_graph": "/chat/knowledge-graph",
                    },
                    default_endpoint="/chat/platform",
                    yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
                    sse_completion_events=["dashboard_complete", "kg_complete"],
                )
        
        elif adapter_type == "sse_streaming":
            # SSE Streaming adapter with enriched output
            base_url = kwargs.get("base_url") or os.getenv("CHAT_BASE_URL", "http://localhost:8000")
            auth_token = kwargs.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")
            
            adapter = SSEStreamingAdapter(
                base_url=base_url,
                headers=kwargs.get("headers", {"Authorization": f"Bearer {auth_token}"} if auth_token else {}),
                context_data=kwargs.get("context_data", {}),
                endpoint=kwargs.get("endpoint", "/chat/stream"),
                completion_events=kwargs.get("completion_events", ["complete", "dashboard_complete", "kg_complete"]),
                tool_call_events=kwargs.get("tool_call_events", ["tool_call", "function_call"]),
                usage_event=kwargs.get("usage_event", "usage"),
                payload_builder=kwargs.get("payload_builder"),
                payload_template=kwargs.get("payload_template"),
                include_uuids=kwargs.get("include_uuids", False),
            )
        
        elif adapter_type == "langfuse":
            # LangfuseAdapter is a placeholder for now
            adapter = LangfuseAdapter()
        
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        # Cache adapter
        self._adapters[adapter_id] = adapter
        
        self.logger.info(f"Created adapter: {adapter_type}")
        return adapter
    
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
    
    async def list_adapters(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        List available adapters.
        
        Returns:
            List of adapter metadata
        """
        adapters = []
        
        # List cached adapters
        for adapter_id, adapter in self._adapters.items():
            adapters.append({
                "id": adapter_id,
                "type": type(adapter).__name__,
            })
        
        # List available adapter types
        available_types = [
            {
                "type": "http",
                "description": "Generic HTTP/REST adapter (recommended)",
                "config_keys": [
                    "base_url",
                    "auth_token",
                    "context_field_name",
                    "context_data",
                    "endpoint_mapping",
                    "default_endpoint",
                    "response_format",
                ],
            },
            {
                "type": "http",  # Use "http" with ml-infra config instead of "ml_infra"
                "description": "ML Infra adapter (compatibility wrapper, use 'http' for new integrations)",
                "config_keys": ["base_url", "auth_token", "account_id", "org_id", "project_id"],
            },
            {
                "type": "langfuse",
                "description": "Langfuse adapter (placeholder)",
            },
        ]
        
        return {
            "cached": adapters,
            "available_types": available_types,
        }
