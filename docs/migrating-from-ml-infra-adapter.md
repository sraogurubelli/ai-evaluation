# Migrating from MLInfraAdapter

The `MLInfraAdapter` has been removed from the core codebase. Teams should create their own custom adapters instead.

## Migration Steps

### Step 1: Create Your Custom Adapter

Create your own adapter file (e.g., `my_team_adapter.py`) in your team's codebase:

```python
from ai_evolution.adapters.http import HTTPAdapter

class MyTeamAdapter(HTTPAdapter):
    """Custom adapter for your team's API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        auth_token: str = "",
        account_id: str = "default",
        org_id: str = "default",
        project_id: str = "default",
    ):
        super().__init__(
            base_url=base_url,
            auth_token=auth_token,
            context_field_name="harness_context",  # Your API's context field
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
```

### Step 2: Update Imports

**Before:**
```python
from ai_evolution.adapters.ml_infra import MLInfraAdapter

adapter = MLInfraAdapter(...)
```

**After:**
```python
from my_team_adapter import MyTeamAdapter  # Your custom adapter

adapter = MyTeamAdapter(...)
```

### Step 3: Update Configuration Files

Update any YAML config files:

**Before:**
```yaml
adapter:
  type: ml_infra
  base_url: "http://localhost:8000"
  auth_token: "${AUTH_TOKEN}"
  account_id: "account-123"
  org_id: "org-456"
  project_id: "project-789"
```

**After:**
```yaml
adapter:
  type: http  # Use HTTPAdapter
  base_url: "http://localhost:8000"
  auth_token: "${AUTH_TOKEN}"
  context_field_name: "harness_context"
  context_data:
    account_id: "account-123"
    org_id: "org-456"
    project_id: "project-789"
  endpoint_mapping:
    dashboard: "/chat/dashboard"
    knowledge_graph: "/chat/knowledge-graph"
  default_endpoint: "/chat/platform"
  yaml_extraction_path: ["capabilities_to_run", -1, "input", "yaml"]
```

Or use your custom adapter class directly in code.

## Benefits

1. **Team Ownership**: Your adapter lives in your codebase, you control it
2. **No Core Dependencies**: Core AI Evolution doesn't need to know about your API
3. **Flexibility**: Customize your adapter for your specific needs
4. **Maintainability**: Update your adapter without affecting other teams

## Need Help?

See [Custom Adapters Guide](custom-adapters.md) for detailed instructions and examples.
