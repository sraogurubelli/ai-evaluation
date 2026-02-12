"""Factory functions for built-in adapters."""

import os
import warnings
from typing import Any

from aieval.adapters.base import Adapter
from aieval.adapters.http import HTTPAdapter
from aieval.adapters.sse_streaming import SSEStreamingAdapter
from aieval.adapters.langfuse import LangfuseAdapter
from aieval.config.settings import get_settings


def create_http_adapter(**config: Any) -> HTTPAdapter:
    """
    Factory function for HTTPAdapter.
    
    Args:
        **config: Configuration for HTTPAdapter:
            - base_url: Base URL for the API server
            - auth_token: Authentication token
            - context_field_name: Field name for context in payload
            - context_data: Context data dictionary
            - endpoint_mapping: Mapping of entity types to endpoints
            - default_endpoint: Default endpoint path
            - response_format: Response format ("json" or "sse")
            - yaml_extraction_path: Path to extract YAML from response
            - sse_completion_events: SSE events that indicate completion
            
    Returns:
        HTTPAdapter instance
    """
    base_url = config.get("base_url") or os.getenv("CHAT_BASE_URL", "http://localhost:8000")
    auth_token = config.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")
    
    return HTTPAdapter(
        base_url=base_url,
        auth_token=auth_token,
        context_field_name=config.get("context_field_name", "context"),
        context_data=config.get("context_data", {}),
        endpoint_mapping=config.get("endpoint_mapping", {}),
        default_endpoint=config.get("default_endpoint", "/chat/platform"),
        response_format=config.get("response_format", "json"),
        yaml_extraction_path=config.get("yaml_extraction_path"),
        sse_completion_events=config.get("sse_completion_events"),
    )


def create_sse_streaming_adapter(**config: Any) -> SSEStreamingAdapter:
    """
    Factory function for SSEStreamingAdapter.
    
    Args:
        **config: Configuration for SSEStreamingAdapter:
            - base_url: Base URL for the API server (defaults to CHAT_BASE_URL env var or config)
            - headers: Custom headers dictionary
            - context_data: Context data dictionary
            - endpoint: SSE streaming endpoint path (defaults to CHAT_ENDPOINT env var or config)
            - completion_events: Event names that indicate completion
            - tool_call_events: Event names that indicate tool calls
            - usage_event: Event name that contains token usage
            - payload_builder: Custom payload builder function
            - payload_template: Payload template dictionary
            - include_uuids: Whether to include conversation/interaction IDs
            
    Returns:
        SSEStreamingAdapter instance
    """
    settings = get_settings()
    
    # Get base_url from config, env var, or settings (in that order)
    # Pass None to adapter so it can read from env/config if not explicitly provided
    base_url = config.get("base_url") if "base_url" in config else None
    auth_token = config.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN") or settings.ml_infra.platform_auth_token
    
    headers = config.get("headers", {})
    if auth_token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Get endpoint from config (pass None to adapter so it can read from env/config if not explicitly provided)
    endpoint = config.get("endpoint") if "endpoint" in config else None
    
    return SSEStreamingAdapter(
        base_url=base_url,
        headers=headers,
        context_data=config.get("context_data", {}),
        endpoint=endpoint,
        completion_events=config.get("completion_events", [
            "complete",
            "dashboard_complete",
            "kg_complete",
            "done",
        ]),
        tool_call_events=config.get("tool_call_events", [
            "tool_call",
            "function_call",
            "tool_execution",
        ]),
        usage_event=config.get("usage_event", "usage"),
        payload_builder=config.get("payload_builder"),
        payload_template=config.get("payload_template"),
        include_uuids=config.get("include_uuids", False),
    )


def create_langfuse_adapter(**config: Any) -> LangfuseAdapter:
    """
    Factory function for LangfuseAdapter.
    
    Args:
        **config: Configuration for LangfuseAdapter (currently unused)
            
    Returns:
        LangfuseAdapter instance
    """
    return LangfuseAdapter()


def create_ml_infra_adapter(**config: Any) -> Adapter:
    """
    Factory function for ml_infra adapter (deprecated, for backward compatibility).
    
    This creates an HTTPAdapter with ml-infra specific configuration.
    For new code, use create_http_adapter with ml-infra config instead.
    
    Args:
        **config: Configuration including:
            - base_url: Base URL for ML Infra API
            - auth_token: Authentication token
            - account_id: Account ID
            - org_id: Organization ID
            - project_id: Project ID
            - use_sse_streaming: If True, use SSEStreamingAdapter instead
            
    Returns:
        HTTPAdapter or SSEStreamingAdapter instance
    """
    warnings.warn(
        "ml_infra adapter type is deprecated. Use 'http' adapter type with ml-infra "
        "configuration instead. See docs/custom-adapters.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )
    
    base_url = config.get("base_url") or os.getenv("CHAT_BASE_URL", "http://localhost:8000")
    auth_token = config.get("auth_token") or os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")
    account_id = config.get("account_id") or os.getenv("ACCOUNT_ID", "default")
    org_id = config.get("org_id") or os.getenv("ORG_ID", "default")
    project_id = config.get("project_id") or os.getenv("PROJECT_ID", "default")
    
    use_sse_streaming = config.get("use_sse_streaming", False)
    
    if use_sse_streaming:
        settings = get_settings()
        return create_sse_streaming_adapter(
            base_url=base_url,
            headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
            context_data={
                "account_id": account_id,
                "org_id": org_id,
                "project_id": project_id,
            },
            endpoint=config.get("endpoint") or settings.ml_infra.endpoint,
            completion_events=["complete", "dashboard_complete", "kg_complete"],
            tool_call_events=["tool_call", "function_call"],
            include_uuids=True,
        )
    else:
        return create_http_adapter(
            base_url=base_url,
            auth_token=auth_token,
            context_field_name="context",
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


def register_builtin_adapters(registry) -> None:
    """
    Register all built-in adapters in the registry.
    
    Args:
        registry: AdapterRegistry instance to register adapters in
    """
    registry.register(
        "http",
        create_http_adapter,
        metadata={
            "description": "Generic HTTP/REST adapter (recommended)",
            "config_keys": [
                "base_url",
                "auth_token",
                "context_field_name",
                "context_data",
                "endpoint_mapping",
                "default_endpoint",
                "response_format",
                "yaml_extraction_path",
                "sse_completion_events",
            ],
        }
    )
    
    registry.register(
        "rest",
        create_http_adapter,  # Alias for http
        metadata={
            "description": "Generic HTTP/REST adapter (alias for 'http')",
            "config_keys": [
                "base_url",
                "auth_token",
                "context_field_name",
                "context_data",
                "endpoint_mapping",
                "default_endpoint",
                "response_format",
            ],
        }
    )
    
    registry.register(
        "sse_streaming",
        create_sse_streaming_adapter,
        metadata={
            "description": "SSE streaming adapter with enriched output (events, tools, metrics)",
            "config_keys": [
                "base_url",
                "headers",
                "context_data",
                "endpoint",
                "completion_events",
                "tool_call_events",
                "usage_event",
                "payload_builder",
                "payload_template",
                "include_uuids",
            ],
        }
    )
    
    registry.register(
        "langfuse",
        create_langfuse_adapter,
        metadata={
            "description": "Langfuse adapter (placeholder)",
            "config_keys": [],
        }
    )
    
    # Register deprecated ml_infra adapter for backward compatibility
    registry.register(
        "ml_infra",
        create_ml_infra_adapter,
        metadata={
            "description": "ML Infra adapter (deprecated - use 'http' with ml-infra config)",
            "config_keys": [
                "base_url",
                "auth_token",
                "account_id",
                "org_id",
                "project_id",
                "use_sse_streaming",
            ],
        }
    )
