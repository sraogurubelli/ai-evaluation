"""Example custom adapter template.

This is a template that teams can use to create their own adapters.
Copy this file and modify it for your team's specific API requirements.
"""

from aieval.adapters.base import Adapter
from typing import Any
import aiohttp
import logging

logger = logging.getLogger(__name__)


class ExampleTeamAdapter(Adapter):
    """
    Example custom adapter for a team's AI system.
    
    This adapter demonstrates how to:
    1. Implement the Adapter interface
    2. Handle authentication
    3. Make API calls
    4. Parse responses
    5. Handle errors
    
    Copy this template and modify for your team's needs.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        team_config: dict[str, Any] | None = None,
    ):
        """
        Initialize adapter.
        
        Args:
            base_url: Base URL for your API
            api_key: API key for authentication
            team_config: Team-specific configuration
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.team_config = team_config or {}
        
        # Set up headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Add team-specific headers if needed
        if "team_id" in self.team_config:
            self.headers["X-Team-ID"] = self.team_config["team_id"]
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate output using your AI system.
        
        Args:
            input_data: Input dictionary containing:
                - prompt: User prompt (required)
                - entity_type: Type of entity (optional)
                - operation_type: Operation type (optional)
                - old_yaml: Existing YAML for updates (optional)
            model: Model name (optional)
            **kwargs: Additional parameters
        
        Returns:
            Generated YAML string or output
        
        Raises:
            RuntimeError: If API call fails
        """
        # Extract input fields
        prompt = input_data.get("prompt", "")
        entity_type = input_data.get("entity_type", "pipeline")
        operation_type = input_data.get("operation_type", "create")
        old_yaml = input_data.get("old_yaml")
        
        # Build payload for your API
        payload = {
            "prompt": prompt,
            "entity_type": entity_type,
            "operation": operation_type,
            "model": model or self.team_config.get("default_model", "gpt-4o"),
        }
        
        # Add old_yaml if present (for updates)
        if old_yaml:
            payload["existing_yaml"] = old_yaml
        
        # Add any team-specific fields
        if "custom_field" in self.team_config:
            payload["custom"] = self.team_config["custom_field"]
        
        # Determine endpoint (customize based on your API)
        endpoint = f"{self.base_url}/api/v1/generate"
        if entity_type in ["dashboard", "knowledge_graph"]:
            endpoint = f"{self.base_url}/api/v1/{entity_type}"
        
        # Make API call
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=300),  # 5 minute timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        raise RuntimeError(
                            f"API call failed with status {response.status}: {error_text}"
                        )
                    
                    result = await response.json()
                    
                    # Extract YAML from response (customize based on your API structure)
                    # Option 1: Direct field
                    if "yaml" in result:
                        return result["yaml"]
                    
                    # Option 2: Nested field
                    if "data" in result and "yaml" in result["data"]:
                        return result["data"]["yaml"]
                    
                    # Option 3: Output field
                    if "output" in result:
                        return result["output"]
                    
                    # Option 4: Return full response as string
                    return str(result)
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise RuntimeError(f"Network error during API call: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


# Usage example:
# adapter = ExampleTeamAdapter(
#     base_url="https://your-api.example.com",
#     api_key="your-api-key",
#     team_config={
#         "team_id": "team-123",
#         "default_model": "gpt-4o",
#     },
# )
# 
# result = await adapter.generate({
#     "prompt": "Create a pipeline",
#     "entity_type": "pipeline",
# })
