"""ML Infra adapter - DEPRECATED.

This adapter has been removed from the core codebase. Teams should create
their own custom adapters instead.

See docs/custom-adapters.md for guidance on creating custom adapters.
See docs/migrating-from-ml-infra-adapter.md for migration instructions.

This file is kept temporarily for reference but will be removed in a future version.
"""

# This file is deprecated and will be removed.
# Teams should use HTTPAdapter with ml-infra configuration instead.
# See docs/custom-adapters.md for examples.


"""ML Infra adapter - compatibility wrapper for HTTPAdapter.

This module provides a compatibility adapter for ml-infra server APIs.
It's a convenience wrapper around HTTPAdapter with ml-infra-specific defaults.

For new integrations, use HTTPAdapter directly with your API configuration.
"""

import uuid
import json
import logging
from typing import Any

import aiohttp

from ai_evolution.adapters.http import HTTPAdapter

logger = logging.getLogger(__name__)


class MLInfraAdapter(HTTPAdapter):
    """
    Compatibility adapter for ml-infra server API.
    
    This is a convenience wrapper around HTTPAdapter with ml-infra-specific
    defaults. It uses "harness_context" as the context field name, which is
    part of the ml-infra API contract.
    
    For new integrations or other APIs, use HTTPAdapter directly.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        auth_token: str = "",
        account_id: str = "default",
        org_id: str = "default",
        project_id: str = "default",
    ):
        """
        Initialize ML Infra adapter (compatibility wrapper).
        
        Args:
            base_url: Base URL for ml-infra server
            auth_token: Authentication token
            account_id: Account ID
            org_id: Organization ID
            project_id: Project ID
        """
        # Configure HTTPAdapter with ml-infra-specific settings
        super().__init__(
            base_url=base_url,
            auth_token=auth_token,
            context_field_name="harness_context",  # ml-infra API uses this field name
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
            response_format="json",  # Most endpoints use JSON, dashboard/KG use SSE
            yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
            sse_completion_events=["dashboard_complete", "kg_complete"],
        )
    
    def _get_endpoint(self, entity_type: str) -> str:
        """
        Get API endpoint for entity type.
        
        Matches ml-infra/evals endpoint selection logic.
        """
        entity_type_lower = entity_type.lower()
        if entity_type_lower == "dashboard":
            return f"{self.base_url}/chat/dashboard"
        elif entity_type_lower == "knowledge_graph":
            return f"{self.base_url}/chat/knowledge-graph"
        else:
            return f"{self.base_url}/chat/platform"
    
    def _generate_payload(
        self,
        prompt: str,
        entity_type: str,
        operation_type: str = "create",
        old_yaml: str | None = None,
        model: str | None = None,
        schema_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate payload for ml-infra API."""
        entity_type_lower = entity_type.lower()
        
        # Special handling for dashboard and knowledge_graph
        if entity_type_lower in ["dashboard", "knowledge_graph"]:
            payload = {
                "prompt": prompt,
                "stream": False,
            }
            if model:
                payload["model"] = model
            if schema_context:
                payload["schema_context"] = schema_context
            return payload
        
        # Standard entity types (pipeline, service, etc.)
        # Determine provider from model name (matching ml-infra/evals logic)
        provider = "openai"  # Default
        if model:
            model_lower = model.lower()
            if "claude" in model_lower:
                provider = "anthropic"
            elif any(x in model_lower for x in ["gpt", "o1", "o3"]):
                provider = "openai"
            # Add more providers as needed
        
        # Determine action (matching ml-infra/evals format: OPERATION_ENTITY)
        entity_upper = entity_type.upper()
        operation_upper = operation_type.upper()
        action = f"{operation_upper}_{entity_upper}"
        
        # Build payload matching ml-infra/evals format exactly
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
            # Note: "harness_context" is part of ml-infra API contract
            "harness_context": {
                "account_id": self.account_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
            },
        }
        
        # Add old YAML for update operations (matching ml-infra/evals format)
        if operation_type.lower() == "update" and old_yaml:
            payload["conversation_raw"] = [
                {"role": "assistant", "content": old_yaml}
            ]
        
        return payload
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate output from input using ml-infra server.
        
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
        
        # Make API call (matching ml-infra/evals timeout and error handling)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"ML Infra API error {response.status}: {error_text}"
                    )
                
                # Parse response based on entity type
                entity_type_lower = entity_type.lower()
                if entity_type_lower in ["dashboard", "knowledge_graph"]:
                    # SSE format for dashboard/KG (matching ml-infra/evals parsing)
                    result_data = None
                    current_event = None
                    
                    try:
                        async for line in response.content:
                            line = line.decode("utf-8").strip()
                            if not line:
                                continue
                            
                            if line.startswith("event:"):
                                current_event = line[6:].strip()
                            elif line.startswith("data:"):
                                data_str = line[5:].strip()
                                if current_event in ["dashboard_complete", "kg_complete"]:
                                    try:
                                        result_data = json.loads(data_str)
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"Failed to parse SSE data for {entity_type}: {e}")
                                        continue
                        
                        if result_data:
                            # Return as JSON string (matching ml-infra/evals format)
                            return json.dumps(result_data)
                        else:
                            raise RuntimeError(f"No completion event received for {entity_type}")
                    except Exception as e:
                        logger.error(f"Error parsing SSE response for {entity_type}: {e}")
                        raise RuntimeError(f"Failed to parse SSE response: {e}")
                else:
                    # JSON response for standard entities (matching ml-infra/evals parsing)
                    try:
                        resp_json = await response.json()
                    except Exception as e:
                        error_text = await response.text()
                        raise RuntimeError(f"Failed to parse JSON response: {e}. Response: {error_text[:500]}")
                    
                    # Extract YAML from capabilities (matching ml-infra/evals logic)
                    capabilities = resp_json.get("capabilities_to_run", [])
                    if capabilities:
                        # Get last capability (most recent)
                        last_capability = capabilities[-1]
                        capability_type = last_capability.get("type")
                        
                        if capability_type == "display_yaml":
                            yaml_content = last_capability.get("input", {}).get("yaml", "")
                            if not yaml_content:
                                raise RuntimeError("display_yaml capability has empty YAML content")
                            return yaml_content
                        elif capability_type == "display_error":
                            error_msg = last_capability.get("input", {}).get("error", "Unknown error")
                            raise RuntimeError(f"ML Infra API returned error: {error_msg}")
                        else:
                            raise RuntimeError(f"Unexpected capability type: {capability_type}")
                    
                    # Fallback: check if response has YAML directly
                    if "yaml" in resp_json:
                        return resp_json["yaml"]
                    
                    raise RuntimeError(f"Unexpected response format. No capabilities_to_run found. Response keys: {list(resp_json.keys())}")
