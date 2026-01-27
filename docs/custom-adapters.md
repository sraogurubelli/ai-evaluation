# Creating Custom Adapters

AI Evolution provides a flexible adapter system that allows teams to integrate with their own AI systems and APIs. Instead of maintaining team-specific adapters in the core codebase, teams should create their own custom adapters.

## Quick Start

### Option 1: Use HTTPAdapter (Recommended for REST APIs)

For most REST APIs, you can use the generic `HTTPAdapter` with your API configuration:

```python
from ai_evolution.adapters.http import HTTPAdapter

# Create adapter for your API
adapter = HTTPAdapter(
    base_url="https://your-api.example.com",
    auth_token="your-auth-token",
    context_field_name="context",  # Your API's context field name
    context_data={
        "account_id": "account-123",
        "org_id": "org-456",
        # Add any other context your API needs
    },
    endpoint_mapping={
        "pipeline": "/api/v1/pipelines",
        "service": "/api/v1/services",
        # Map entity types to your API endpoints
    },
    default_endpoint="/api/v1/chat",  # Default endpoint
    response_format="json",  # or "sse" for Server-Sent Events
    yaml_extraction_path=["result", "yaml"],  # Path to extract YAML from response
)
```

### Option 2: Create a Custom Adapter Class

For more complex integrations or non-REST APIs, create your own adapter:

```python
from ai_evolution.adapters.base import Adapter
from typing import Any
import aiohttp

class MyTeamAdapter(Adapter):
    """Custom adapter for My Team's AI system."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        team_id: str,
    ):
        """
        Initialize adapter.
        
        Args:
            base_url: Base URL for your API
            api_key: API key for authentication
            team_id: Team identifier
        """
        self.base_url = base_url
        self.api_key = api_key
        self.team_id = team_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-Team-ID": team_id,
        }
    
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
                - prompt: User prompt
                - entity_type: Type of entity (pipeline, service, etc.)
                - operation_type: Operation (create, update, etc.)
                - old_yaml: (optional) Existing YAML for updates
            model: Model name to use
            **kwargs: Additional parameters
        
        Returns:
            Generated YAML string or output
        """
        prompt = input_data.get("prompt", "")
        entity_type = input_data.get("entity_type", "pipeline")
        
        # Build payload for your API
        payload = {
            "prompt": prompt,
            "entity_type": entity_type,
            "model": model or "default-model",
        }
        
        # Add old_yaml if present (for updates)
        if input_data.get("old_yaml"):
            payload["existing_yaml"] = input_data["old_yaml"]
        
        # Make API call
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=self.headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                # Extract YAML from response (adjust based on your API structure)
                return result.get("yaml", result.get("output", ""))
```

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
                - Any other fields your API needs
            model: Model name (optional)
            **kwargs: Additional parameters
        
        Returns:
            Generated output (typically YAML string)
        """
        # Your implementation
        pass
```

## Common Patterns

### Pattern 1: REST API with JSON Response

```python
from ai_evolution.adapters.http import HTTPAdapter

adapter = HTTPAdapter(
    base_url="https://api.example.com",
    auth_token="token",
    response_format="json",
    yaml_extraction_path=["data", "yaml"],  # Extract from response["data"]["yaml"]
)
```

### Pattern 2: REST API with SSE (Server-Sent Events)

```python
from ai_evolution.adapters.http import HTTPAdapter

adapter = HTTPAdapter(
    base_url="https://api.example.com",
    auth_token="token",
    response_format="sse",
    sse_completion_events=["complete", "done"],  # Events that indicate completion
)
```

### Pattern 3: Custom Payload Structure

If your API requires a different payload structure, override `_generate_payload`:

```python
from ai_evolution.adapters.http import HTTPAdapter

class MyCustomHTTPAdapter(HTTPAdapter):
    def _generate_payload(self, prompt, entity_type, **kwargs):
        # Custom payload structure
        return {
            "query": prompt,
            "type": entity_type,
            "metadata": self.context_data,
        }
```

### Pattern 4: Custom Response Parsing

If your API returns data in a different format:

```python
from ai_evolution.adapters.http import HTTPAdapter

class MyCustomHTTPAdapter(HTTPAdapter):
    async def generate(self, input_data, model=None, **kwargs):
        # Make request
        response = await super()._make_request(...)
        
        # Custom parsing
        if "custom_field" in response:
            return response["custom_field"]["content"]
        
        # Fallback to default parsing
        return super().generate(input_data, model, **kwargs)
```

## Testing Your Adapter

Create tests for your adapter:

```python
import pytest
from my_team_adapter import MyTeamAdapter

@pytest.mark.asyncio
async def test_adapter_generate():
    """Test adapter generates output."""
    adapter = MyTeamAdapter(
        base_url="http://test-server",
        api_key="test-key",
        team_id="test-team",
    )
    
    result = await adapter.generate(
        {
            "prompt": "Create a pipeline",
            "entity_type": "pipeline",
        },
        model="gpt-4o",
    )
    
    assert result is not None
    assert isinstance(result, str)
```

## Sharing Your Adapter

1. **Keep it in your team's repository** - Don't add team-specific adapters to the core AI Evolution codebase
2. **Document the configuration** - Provide clear examples of how to use your adapter
3. **Share examples** - If your adapter pattern is useful, share it as an example for other teams

## Migration from ml_infra Adapter

If you were using `MLInfraAdapter`, migrate to `HTTPAdapter`:

**Before:**
```python
from ai_evolution.adapters.ml_infra import MLInfraAdapter

adapter = MLInfraAdapter(
    base_url="http://localhost:8000",
    auth_token="token",
    account_id="acc-123",
    org_id="org-456",
    project_id="proj-789",
)
```

**After:**
```python
from ai_evolution.adapters.http import HTTPAdapter

adapter = HTTPAdapter(
    base_url="http://localhost:8000",
    auth_token="token",
    context_field_name="harness_context",
    context_data={
        "account_id": "acc-123",
        "org_id": "org-456",
        "project_id": "proj-789",
    },
    endpoint_mapping={
        "dashboard": "/chat/dashboard",
        "knowledge_graph": "/chat/knowledge-graph",
    },
    default_endpoint="/chat/platform",
    yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
)
```

## Examples

See `examples/adapters/` for example adapter implementations that teams can use as templates.
