# Domain Abstraction for DevOps/DevSecOps Agents

## Overview

AI Evolution is designed to be domain-agnostic. This document explains how to adapt it for DevOps, DevSecOps, or any other agent type.

## Core Abstractions

### 1. **Domain-Agnostic Core** (Already Generic)

The core framework is already domain-agnostic:

- **`Experiment`** - Works with any dataset/scorer combination
- **`DatasetItem`** - Generic input/output/expected structure
- **`Score`** - Generic scoring result
- **`Adapter`** - Interface for any AI system

### 2. **Domain-Specific Extensions**

Domain-specific logic lives in:

- **Scorers** - Domain-specific evaluation logic
- **Adapters** - Domain-specific API integrations
- **Datasets** - Domain-specific data formats
- **Sinks** - Domain-specific output formats

## Abstraction Layers

```
┌─────────────────────────────────────────────────────────┐
│  Domain Layer (DevOps/DevSecOps/ML Infra/etc.)        │
│  - Domain-specific scorers                             │
│  - Domain-specific adapters                             │
│  - Domain-specific datasets                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Abstraction Layer (Generic Interfaces)                │
│  - Scorer interface                                    │
│  - Adapter interface                                   │
│  - Dataset loader interface                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Core Framework (Domain-Agnostic)                       │
│  - Experiment orchestrator                             │
│  - Run tracking                                        │
│  - Comparison utilities                                │
└─────────────────────────────────────────────────────────┘
```

## Extension Points

### 1. **Scorer Interface** (Domain-Specific Logic)

```python
from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score

class DevOpsScorer(Scorer):
    """Example: DevOps-specific scorer."""
    
    def score(self, generated: Any, expected: Any, metadata: dict) -> Score:
        # Domain-specific evaluation logic
        # e.g., Check if Kubernetes YAML is valid
        # e.g., Verify Terraform config correctness
        # e.g., Validate Dockerfile best practices
        pass
```

### 2. **Adapter Interface** (Domain-Specific APIs)

```python
from ai_evolution.adapters.base import Adapter

class DevOpsAdapter(Adapter):
    """Example: DevOps agent adapter."""
    
    async def generate(self, input_data: dict, **kwargs) -> str:
        # Call DevOps agent API
        # e.g., Kubernetes config generator
        # e.g., Terraform generator
        # e.g., CI/CD pipeline generator
        pass
```

### 3. **Dataset Loaders** (Domain-Specific Formats)

```python
def load_devops_dataset(file_path: str) -> list[DatasetItem]:
    """Load DevOps-specific dataset format."""
    # e.g., Load Kubernetes test cases
    # e.g., Load Terraform test cases
    # e.g., Load CI/CD pipeline test cases
    pass
```

## DevOps/DevSecOps Examples

### Example 1: Kubernetes Config Generation

```python
from ai_evolution import Experiment, HTTPAdapter
from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score, DatasetItem

class KubernetesValidScorer(Scorer):
    """Validates Kubernetes YAML correctness."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        import yaml
        try:
            k8s_config = yaml.safe_load(generated)
            # Validate Kubernetes schema
            is_valid = self._validate_k8s_schema(k8s_config)
            return Score(
                name="k8s_valid",
                value=is_valid,
                eval_id="k8s_valid.v1",
                comment="Kubernetes config validation",
            )
        except Exception as e:
            return Score(
                name="k8s_valid",
                value=False,
                eval_id="k8s_valid.v1",
                comment=f"Invalid YAML: {e}",
            )

# Create experiment
experiment = Experiment(
    name="kubernetes_config_generation",
    dataset=[
        DatasetItem(
            id="k8s-1",
            input={"prompt": "Create a deployment for nginx"},
            expected={"kind": "Deployment", "apiVersion": "apps/v1"},
        )
    ],
    scorers=[KubernetesValidScorer()],
)

# Run with DevOps agent
adapter = HTTPAdapter(base_url="http://devops-agent:8000")
result = await experiment.run(adapter=adapter, model="gpt-4")
```

### Example 2: Terraform Configuration

```python
class TerraformValidScorer(Scorer):
    """Validates Terraform configuration."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        # Run terraform validate
        # Check resource structure
        # Verify best practices
        pass

class TerraformSecurityScorer(Scorer):
    """Checks Terraform security best practices."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        # Check for hardcoded secrets
        # Verify encryption settings
        # Validate IAM policies
        pass

experiment = Experiment(
    name="terraform_generation",
    dataset=load_terraform_dataset("datasets/terraform.jsonl"),
    scorers=[
        TerraformValidScorer(),
        TerraformSecurityScorer(),  # DevSecOps!
    ],
)
```

### Example 3: CI/CD Pipeline Generation

```python
class CICDPipelineScorer(Scorer):
    """Evaluates CI/CD pipeline quality."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        # Check pipeline structure
        # Verify security scanning steps
        # Validate test stages
        # Check deployment gates
        pass

experiment = Experiment(
    name="cicd_pipeline_generation",
    dataset=load_cicd_dataset("datasets/cicd.jsonl"),
    scorers=[CICDPipelineScorer()],
)
```

### Example 4: Dockerfile Generation

```python
class DockerfileSecurityScorer(Scorer):
    """Checks Dockerfile security best practices."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        # Check for root user
        # Verify no hardcoded secrets
        # Check for outdated base images
        # Validate multi-stage builds
        pass

class DockerfileOptimizationScorer(Scorer):
    """Checks Dockerfile optimization."""
    
    def score(self, generated: str, expected: dict, metadata: dict) -> Score:
        # Check layer caching
        # Verify .dockerignore usage
        # Check image size
        pass
```

## Plugin System Architecture

### 1. **Scorer Registry**

```python
# src/ai_evolution/scorers/registry.py
SCORER_REGISTRY = {
    "deep_diff": DeepDiffScorer,
    "schema_validation": SchemaValidationScorer,
    # Domain-specific scorers
    "k8s_valid": KubernetesValidScorer,
    "terraform_valid": TerraformValidScorer,
    "dockerfile_security": DockerfileSecurityScorer,
}

def create_scorer(scorer_type: str, **config) -> Scorer:
    """Create scorer from registry."""
    scorer_class = SCORER_REGISTRY.get(scorer_type)
    if not scorer_class:
        raise ValueError(f"Unknown scorer type: {scorer_type}")
    return scorer_class(**config)
```

### 2. **Domain Presets**

```python
# examples/devops/presets.py
DEVOPS_SCORERS = {
    "kubernetes": [
        KubernetesValidScorer(),
        KubernetesSecurityScorer(),
    ],
    "terraform": [
        TerraformValidScorer(),
        TerraformSecurityScorer(),
        TerraformBestPracticesScorer(),
    ],
    "dockerfile": [
        DockerfileSecurityScorer(),
        DockerfileOptimizationScorer(),
    ],
    "cicd": [
        CICDPipelineScorer(),
        CICDSecurityScorer(),
    ],
}

def create_devops_experiment(
    domain: str,
    dataset: list[DatasetItem],
) -> Experiment:
    """Create pre-configured DevOps experiment."""
    scorers = DEVOPS_SCORERS.get(domain, [])
    return Experiment(
        name=f"{domain}_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
```

## Configuration-Driven Approach

### YAML Config for DevOps

```yaml
# examples/devops/config.yaml
experiment:
  name: "kubernetes_config_generation"
  
dataset:
  type: "jsonl"
  path: "datasets/k8s_test_cases.jsonl"

adapter:
  type: "http"
  base_url: "http://devops-agent:8000"
  endpoint: "/generate/k8s"

scorers:
  - type: "k8s_valid"
  - type: "k8s_security"
  - type: "k8s_best_practices"

sinks:
  - type: "csv"
    path: "results/k8s_eval.csv"
  - type: "json"
    path: "results/k8s_eval.json"
```

## Best Practices

### 1. **Separate Domain Logic**

- Keep domain-specific logic in separate modules
- Use the core framework for orchestration
- Don't hardcode domain assumptions in core

### 2. **Use Composition**

- Compose multiple scorers for comprehensive evaluation
- Mix generic scorers (DeepDiff) with domain-specific ones
- Create domain presets for common use cases

### 3. **Extensible Design**

- Implement the `Scorer` interface for custom logic
- Use `HTTPAdapter` for any REST API
- Create custom dataset loaders for domain formats

### 4. **Reusable Patterns**

- Create base classes for common patterns
- Share utilities across domains
- Document domain-specific extensions

## Migration Path

1. **Start Generic**: Use existing generic scorers (DeepDiff, Schema)
2. **Add Domain Logic**: Create domain-specific scorers
3. **Create Presets**: Build domain-specific presets
4. **Share Patterns**: Extract reusable patterns

## Next Steps

1. Create `examples/devops/` directory with examples
2. Implement DevOps-specific scorers
3. Create DevOps adapter examples
4. Document domain extension patterns
