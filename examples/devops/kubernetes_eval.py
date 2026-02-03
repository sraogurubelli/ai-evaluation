"""Example: Kubernetes Config Generation Evaluation.

This demonstrates how to evaluate a DevOps agent that generates Kubernetes configurations.
"""

import asyncio
import yaml
from typing import Any

from aieval import Experiment, HTTPAdapter, DatasetItem
from aieval.scorers.base import Scorer
from aieval.core.types import Score


class KubernetesValidScorer(Scorer):
    """Validates Kubernetes YAML correctness."""
    
    def score(
        self,
        generated: Any,
        expected: dict[str, Any] | None,
        metadata: dict[str, Any],
    ) -> Score:
        """Score Kubernetes config validity."""
        if isinstance(generated, str):
            try:
                config = yaml.safe_load(generated)
            except yaml.YAMLError as e:
                return Score(
                    name=self.name,
                    value=False,
                    eval_id=self.eval_id,
                    comment=f"Invalid YAML: {e}",
                    metadata=metadata,
                )
        else:
            config = generated
        
        # Basic validation
        is_valid = (
            isinstance(config, dict) and
            "kind" in config and
            "apiVersion" in config
        )
        
        # Check expected kind if provided
        if expected and "kind" in expected:
            is_valid = is_valid and config.get("kind") == expected["kind"]
        
        return Score(
            name=self.name,
            value=is_valid,
            eval_id=self.eval_id,
            comment="Kubernetes config validation",
            metadata={**metadata, "kind": config.get("kind")},
        )


class KubernetesSecurityScorer(Scorer):
    """Checks Kubernetes security best practices."""
    
    def score(
        self,
        generated: Any,
        expected: dict[str, Any] | None,
        metadata: dict[str, Any],
    ) -> Score:
        """Score Kubernetes security practices."""
        if isinstance(generated, str):
            try:
                config = yaml.safe_load(generated)
            except yaml.YAMLError:
                return Score(
                    name=self.name,
                    value=0.0,
                    eval_id=self.eval_id,
                    comment="Invalid YAML",
                    metadata=metadata,
                )
        else:
            config = generated
        
        security_score = 1.0
        issues = []
        
        # Check for security contexts
        if "spec" in config:
            spec = config["spec"]
            if "template" in spec:
                template = spec["template"]
                if "spec" in template:
                    pod_spec = template["spec"]
                    
                    # Check for runAsNonRoot
                    security_context = pod_spec.get("securityContext", {})
                    if not security_context.get("runAsNonRoot"):
                        security_score -= 0.3
                        issues.append("Missing runAsNonRoot")
                    
                    # Check containers
                    containers = pod_spec.get("containers", [])
                    for container in containers:
                        container_ctx = container.get("securityContext", {})
                        if not container_ctx.get("readOnlyRootFilesystem"):
                            security_score -= 0.2
                            issues.append("Missing readOnlyRootFilesystem")
                        if container_ctx.get("privileged"):
                            security_score -= 0.5
                            issues.append("Container runs as privileged")
        
        security_score = max(0.0, security_score)
        
        return Score(
            name=self.name,
            value=security_score,
            eval_id=self.eval_id,
            comment=f"Security score: {security_score:.2%}. Issues: {', '.join(issues) if issues else 'None'}",
            metadata={**metadata, "issues": issues},
        )


async def main():
    """Run Kubernetes evaluation example."""
    print("=== Kubernetes Config Generation Evaluation ===\n")
    
    # Create dataset
    dataset = [
        DatasetItem(
            id="k8s-1",
            input={
                "prompt": "Create a deployment for nginx with 3 replicas",
                "entity_type": "deployment",
            },
            expected={"kind": "Deployment", "apiVersion": "apps/v1"},
        ),
        DatasetItem(
            id="k8s-2",
            input={
                "prompt": "Create a service for nginx on port 80",
                "entity_type": "service",
            },
            expected={"kind": "Service", "apiVersion": "v1"},
        ),
    ]
    
    # Create experiment with DevOps scorers
    experiment = Experiment(
        name="kubernetes_config_generation",
        dataset=dataset,
        scorers=[
            KubernetesValidScorer(name="k8s_valid", eval_id="k8s_valid.v1"),
            KubernetesSecurityScorer(name="k8s_security", eval_id="k8s_security.v1"),
        ],
    )
    
    # Create adapter for DevOps agent
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",  # Your DevOps agent URL
        endpoint="/generate/k8s",
    )
    
    # Run experiment
    print("Running experiment...")
    result = await experiment.run(
        adapter=adapter,
        model="gpt-4",
        concurrency_limit=2,
    )
    
    # Print results
    print(f"\nExperiment completed: {result.run_id}")
    print(f"Total scores: {len(result.scores)}")
    print("\nScore summary:")
    for score in result.scores:
        print(f"  {score.name}: {score.value} - {score.comment}")


if __name__ == "__main__":
    asyncio.run(main())
