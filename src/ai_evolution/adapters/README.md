# Adapters

Adapters provide integration with different AI systems and APIs. **Teams should create their own custom adapters** rather than adding team-specific adapters to the core codebase.

## HTTPAdapter (Recommended)

Generic HTTP/REST adapter that can be configured for any API. This is the recommended approach for most integrations.

**Usage**:
```python
from ai_evolution.adapters.http import HTTPAdapter

# Basic configuration
adapter = HTTPAdapter(
    base_url="http://localhost:8000",
    auth_token="your-token",
)

# Advanced configuration with custom context and endpoints
adapter = HTTPAdapter(
    base_url="https://your-api.example.com",
    auth_token="your-token",
    context_field_name="context",  # Your API's context field name
    context_data={
        "account_id": "account-123",
        "org_id": "org-456",
        # Add any context your API requires
    },
    endpoint_mapping={
        "dashboard": "/chat/dashboard",
        "knowledge_graph": "/chat/knowledge-graph",
        # Map entity types to your API endpoints
    },
    default_endpoint="/chat/platform",  # Default endpoint
    response_format="json",  # or "sse" for Server-Sent Events
    yaml_extraction_path=["result", "yaml"],  # Path to extract YAML from JSON response
    sse_completion_events=["complete", "done"],  # SSE events that indicate completion
)
```

## Creating Custom Adapters

**Teams should create their own adapters** for their specific AI systems. See [Custom Adapters Guide](../docs/custom-adapters.md) for detailed instructions.

### Quick Example

```python
from ai_evolution.adapters.base import Adapter
from typing import Any
import aiohttp

class MyTeamAdapter(Adapter):
    """Custom adapter for My Team's AI system."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate output using your AI system."""
        prompt = input_data.get("prompt", "")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "model": model},
                headers=self.headers,
            ) as response:
                result = await response.json()
                return result.get("yaml", result.get("output", ""))
```

See `examples/adapters/example_custom_adapter.py` for a complete template.

## Adapter Interface

All adapters must implement the `Adapter` interface:

```python
from ai_evolution.adapters.base import Adapter
from typing import Any

class MyAdapter(Adapter):
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate output from input.
        
        Args:
            input_data: Dictionary containing:
                - prompt: User prompt (required)
                - entity_type: Entity type (optional)
                - operation_type: Operation type (optional)
                - old_yaml: Existing YAML for updates (optional)
            model: Model name (optional)
            **kwargs: Additional parameters
        
        Returns:
            Generated output (typically YAML string)
        """
        # Your implementation
        pass
```

## Resources

- [Custom Adapters Guide](../docs/custom-adapters.md) - Comprehensive guide for creating adapters
- [Example Adapter Template](../examples/adapters/example_custom_adapter.py) - Template to copy and modify
- [HTTPAdapter Source](../src/ai_evolution/adapters/http.py) - Reference implementation
