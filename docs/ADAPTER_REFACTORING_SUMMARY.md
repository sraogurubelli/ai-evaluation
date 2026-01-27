# Adapter Refactoring Summary

## Overview

The `MLInfraAdapter` has been removed from the core codebase. Teams should now create their own custom adapters instead of adding team-specific adapters to the core.

## Changes Made

### 1. Documentation Created

- **`docs/custom-adapters.md`** - Comprehensive guide for creating custom adapters
  - Quick start with HTTPAdapter
  - Custom adapter implementation guide
  - Common patterns and examples
  - Testing guidance
  - Migration from ml_infra adapter

- **`docs/migrating-from-ml-infra-adapter.md`** - Step-by-step migration guide

- **`examples/adapters/example_custom_adapter.py`** - Complete template for teams to copy

- **`examples/adapters/README.md`** - Examples directory documentation

### 2. Code Updates

#### Adapters Module
- **`src/ai_evolution/adapters/__init__.py`** - Removed MLInfraAdapter export, added deprecation notice
- **`src/ai_evolution/adapters/README.md`** - Updated to emphasize custom adapters
- **`src/ai_evolution/adapters/ml_infra.py`** - Added deprecation notice (kept for reference)

#### Core Modules
- **`src/ai_evolution/__init__.py`** - Removed MLInfraAdapter from exports
- **`src/ai_evolution/sdk/__init__.py`** - Removed MLInfraAdapter from exports
- **`src/ai_evolution/sdk/ml_infra.py`** - Updated to use HTTPAdapter instead of MLInfraAdapter
- **`src/ai_evolution/sdk/task.py`** - Updated documentation references

#### Agents
- **`src/ai_evolution/agents/adapter_agent.py`** - ml_infra type now uses HTTPAdapter with deprecation warning
- **`src/ai_evolution/agents/experiment_agent.py`** - Updated default adapter type to "http"

#### Tasks & CLI
- **`src/ai_evolution/tasks/manager.py`** - ml_infra type now uses HTTPAdapter with deprecation warning
- **`src/ai_evolution/cli/main.py`** - ml_infra type now uses HTTPAdapter with deprecation warning

#### API & UI
- **`src/ai_evolution/api/models.py`** - Updated adapter type descriptions
- **`src/ai_evolution/ui/gradio_app.py`** - Removed ml_infra from dropdown options

## Migration Path

### For Teams Using MLInfraAdapter

1. **Option 1: Use HTTPAdapter** (Recommended)
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

2. **Option 2: Create Custom Adapter**
   - Copy `examples/adapters/example_custom_adapter.py`
   - Modify for your team's API requirements
   - Keep it in your team's codebase

## Backward Compatibility

- The `ml_infra` adapter type still works but shows a deprecation warning
- It now uses HTTPAdapter internally with ml-infra configuration
- Teams should migrate to using `http` adapter type or create custom adapters

## Benefits

1. **Team Ownership**: Teams control their own adapters
2. **No Core Bloat**: Core codebase doesn't include team-specific code
3. **Flexibility**: Teams can customize adapters for their specific needs
4. **Maintainability**: Teams update their adapters independently

## Next Steps for Teams

1. Review `docs/custom-adapters.md` for guidance
2. Create your team's custom adapter (or use HTTPAdapter)
3. Update your code to use the new adapter
4. Remove any dependencies on MLInfraAdapter
