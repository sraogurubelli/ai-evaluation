"""HTTP/REST adapter for AI system APIs.

This adapter provides a generic HTTP-based adapter that can be configured
to work with different AI system APIs. It supports:
- Configurable endpoint mapping
- Configurable payload structure
- JSON and SSE response parsing
- Custom context field names
"""

import os
import uuid
import json
import logging
from typing import Any

import aiohttp
import yaml

from aieval.adapters.base import Adapter

logger = logging.getLogger(__name__)


class HTTPAdapter(Adapter):
    """
    Generic HTTP adapter for AI system APIs.
    
    This adapter can be configured to work with different API formats by
    specifying endpoint mappings, payload structure, and response parsing.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        auth_token: str = "",
        # Context configuration (for APIs that require context)
        context_field_name: str = "context",  # Field name for context in payload
        context_data: dict[str, Any] | None = None,  # Context data (account_id, org_id, etc.)
        # Endpoint configuration
        endpoint_mapping: dict[str, str] | None = None,  # entity_type -> endpoint path
        default_endpoint: str = "/chat/platform",  # Default endpoint path
        # Response parsing configuration
        response_format: str = "json",  # "json" or "sse"
        yaml_extraction_path: list[str] | None = None,  # Path to extract YAML from response
        sse_completion_events: list[str] | None = None,  # SSE events that indicate completion
    ):
        """
        Initialize HTTP adapter.
        
        Args:
            base_url: Base URL for the API server
            auth_token: Authentication token
            context_field_name: Field name for context in API payload (e.g., "context", "harness_context")
            context_data: Context data dictionary (e.g., {"account_id": "...", "org_id": "..."})
            endpoint_mapping: Mapping of entity types to endpoint paths
                Example: {"dashboard": "/chat/dashboard", "knowledge_graph": "/chat/knowledge-graph"}
            default_endpoint: Default endpoint path for entity types not in mapping
            response_format: Response format ("json" or "sse")
            yaml_extraction_path: Path to extract YAML from JSON response
                Example: ["capabilities_to_run", -1, "input", "yaml"]
            sse_completion_events: List of SSE event names that indicate completion
                Example: ["dashboard_complete", "kg_complete"]
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.context_field_name = context_field_name
        self.context_data = context_data or {}
        self.endpoint_mapping = endpoint_mapping or {}
        self.default_endpoint = default_endpoint
        self.response_format = response_format
        self.yaml_extraction_path = yaml_extraction_path or ["capabilities_to_run", -1, "input", "yaml"]
        self.sse_completion_events = sse_completion_events or ["dashboard_complete", "kg_complete"]
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}" if auth_token else "",
        }
    
    def _get_endpoint(self, entity_type: str) -> str:
        """Get API endpoint for entity type."""
        endpoint_path = self.endpoint_mapping.get(entity_type.lower(), self.default_endpoint)
        return f"{self.base_url}{endpoint_path}"
    
    def _determine_provider(self, model: str | None) -> str:
        """Determine provider from model name."""
        if not model:
            return "openai"
        if "claude" in model.lower():
            return "anthropic"
        elif any(x in model.lower() for x in ["gpt", "o1", "o3"]):
            return "openai"
        return "openai"
    
    def _generate_payload(
        self,
        prompt: str,
        entity_type: str,
        operation_type: str = "create",
        old_yaml: str | None = None,
        model: str | None = None,
        schema_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate payload for API request."""
        entity_type_lower = entity_type.lower()
        
        # Check if this entity type uses a simplified payload format
        # (typically for dashboard/knowledge_graph endpoints)
        if entity_type_lower in self.endpoint_mapping:
            # Simplified format for special endpoints
            payload = {
                "prompt": prompt,
                "stream": False,
            }
            if model:
                payload["model"] = model
            if schema_context:
                payload["schema_context"] = schema_context
            return payload
        
        # Standard payload format
        provider = self._determine_provider(model)
        entity_upper = entity_type.upper()
        operation_upper = operation_type.upper()
        action = f"{operation_upper}_{entity_upper}"
        
        payload = {
            "prompt": prompt,
            "conversation_id": str(uuid.uuid4()),
            "interaction_id": str(uuid.uuid4()),
            "provider": provider,
            "model_name": model,
            "action": action,
            "conversation_raw": [],
            "capabilities": [
                {"type": "display_yaml", "version": "0"},
                {"type": "display_error", "version": "0"},
            ],
            "context": [],
        }
        
        # Add context if configured
        if self.context_data:
            payload[self.context_field_name] = self.context_data
        
        # Add old YAML for update operations
        if operation_type.lower() == "update" and old_yaml:
            payload["conversation_raw"] = [
                {"role": "assistant", "content": old_yaml}
            ]
        
        return payload
    
    def _extract_yaml_from_json(self, resp_json: dict[str, Any]) -> str:
        """Extract YAML from JSON response using configured path."""
        current = resp_json
        for key in self.yaml_extraction_path:
            if isinstance(current, list):
                # Handle negative indices: -1 is valid for any non-empty list
                if (key >= 0 and key < len(current)) or (key < 0 and abs(key) <= len(current)):
                    current = current[key]
                else:
                    raise RuntimeError(f"Cannot access list index {key} in response (list length: {len(current)})")
            else:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    raise RuntimeError(f"Cannot access key '{key}' in response")
        
        if isinstance(current, str):
            return current
        elif isinstance(current, dict) and "yaml" in current:
            return current["yaml"]
        else:
            raise RuntimeError(f"Unexpected YAML format at extraction path: {current}")
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate output from input using HTTP API.
        
        Args:
            input_data: Input data with keys:
                - prompt: User prompt
                - entity_type: Entity type (pipeline, service, dashboard, etc.)
                - operation_type: Operation type (create, update, insights)
                - old_yaml: Old YAML for update operations (optional)
                - schema_context: Schema context for dashboard/KG (optional)
            model: Model name (optional)
            **kwargs: Additional parameters
            
        Returns:
            Generated YAML/JSON string
        """
        logger.info("HTTP adapter invoked")
        prompt = input_data.get("prompt", "")
        entity_type = input_data.get("entity_type", "pipeline")
        operation_type = input_data.get("operation_type", "create")
        old_yaml = input_data.get("old_yaml")
        schema_context = input_data.get("schema_context")
        
        # Generate payload
        payload = self._generate_payload(
            prompt=prompt,
            entity_type=entity_type,
            operation_type=operation_type,
            old_yaml=old_yaml,
            model=model,
            schema_context=schema_context,
        )
        
        # Get endpoint
        endpoint = self._get_endpoint(entity_type)
        
        # Make API call
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"API error {response.status}: {error_text}"
                    )
                logger.debug("=" * 80)
                logger.debug(f"HTTP Response Status: {response.status}")
                logger.debug(f"Content-Type: {response.headers.get('content-type')}")
                logger.debug("=" * 80)
                # Parse response based on format
                # Check if this entity uses SSE (dashboard/KG typically do)
                use_sse = (
                    self.response_format == "sse" or
                    entity_type.lower() in self.endpoint_mapping or
                    response.headers.get("content-type", "").startswith("text/event-stream")
                )
                logger.debug(f"SSE Detection: use_sse={use_sse}")
                logger.debug(f"  - response_format: {self.response_format}")
                logger.debug(f"  - entity_type in mapping: {entity_type.lower() in self.endpoint_mapping}")
                logger.debug(f"  - content-type header: {response.headers.get('content-type')}")
                
                if use_sse:
                    # SSE format
                    logger.info("HTTP adapter: SSE events receiving")
                    result_data = None
                    current_event = None
                    
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue
                        
                        if line.startswith("event:"):
                            current_event = line[6:].strip()
                            logger.debug(f"HTTP adapter: SSE event received: {current_event}")
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            if current_event in self.sse_completion_events:
                                try:
                                    result_data = json.loads(data_str)
                                    logger.info(f"HTTP adapter: SSE completion event received: {current_event}")
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse SSE data: {e}")
                    
                    if result_data:
                        return json.dumps(result_data)
                    else:
                        raise RuntimeError("No completion event received")
                else:
                    # JSON response
                    resp_json = await response.json()
                    logger.debug("=" * 80)
                    logger.debug("JSON RESPONSE RECEIVED")
                    logger.debug("=" * 80)
                    logger.debug(f"Response type: {type(resp_json)}")
                    logger.debug(f"Response keys: {list(resp_json.keys()) if isinstance(resp_json, dict) else 'not a dict'}")
                    logger.debug(f"Full response: {json.dumps(resp_json, indent=2)}")
                    if isinstance(resp_json, dict) and "capabilities_to_run" in resp_json:
                        caps = resp_json["capabilities_to_run"]
                        logger.info(f"capabilities_to_run length: {len(caps) if isinstance(caps, list) else 'not a list'}")
                        logger.info(f"capabilities_to_run: {caps}")
                    logger.info("=" * 80)
                    # Extract YAML using configured path
                    try:
                        yaml_content = self._extract_yaml_from_json(resp_json)
                        if yaml_content:
                            return yaml_content
                    except RuntimeError as e:
                        # Check for error in capabilities
                        capabilities = resp_json.get("capabilities_to_run", [])

                        logger.error(f"YAML extraction failed: {e}")
                        logger.error(f"capabilities_to_run: {capabilities}")
                        logger.error(f"capabilities_to_run length: {len(capabilities)}")
                        logger.info("=" * 80)

                        if capabilities:
                            last_capability = capabilities[-1]
                            if last_capability.get("type") == "display_error":
                                error_msg = last_capability.get("input", {}).get("error", "")
                                raise RuntimeError(f"API error: {error_msg}")
                        raise RuntimeError(f"Failed to extract YAML: {e}")
                    
                    raise RuntimeError("Unexpected response format")
