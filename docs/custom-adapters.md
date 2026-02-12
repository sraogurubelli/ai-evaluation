# Custom Adapters

Connect to your AI system via the `Adapter` interface or `HTTPAdapter`.

## Option 1: HTTPAdapter (REST APIs)

Configure `HTTPAdapter` for your API:

```python
from aieval.adapters.http import HTTPAdapter

adapter = HTTPAdapter(
    base_url="https://your-api.example.com",
    auth_token="your-token",
    context_field_name="context",
    context_data={"account_id": "123", "org_id": "456"},
    endpoint_mapping={"pipeline": "/api/pipelines", "service": "/api/services"},
    default_endpoint="/api/chat",
    response_format="json",  # or "sse"
    yaml_extraction_path=["result", "yaml"],
)
```

## Option 2: Custom adapter class

Implement the `Adapter` interface (method `generate(input_data, model, **kwargs) -> str`). See `aieval.adapters.base.Adapter`.

```python
from aieval.adapters.base import Adapter

class MyAdapter(Adapter):
    async def generate(self, input_data, model=None, **kwargs):
        # Call your API, return generated output string
        ...
```

## Example

Full example: [examples/adapters/example_custom_adapter.py](../examples/adapters/example_custom_adapter.py). For DevOps-style usage: [samples_sdk/consumers/devops](../samples_sdk/consumers/devops).
