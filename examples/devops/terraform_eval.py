"""Example: Terraform Configuration Evaluation.

This demonstrates how to evaluate a DevOps agent that generates Terraform configurations.
"""

import asyncio
import json
from typing import Any

from ai_evolution import Experiment, HTTPAdapter, DatasetItem
from ai_evolution.scorers.base import Scorer
from ai_evolution.core.types import Score


class TerraformValidScorer(Scorer):
    """Validates Terraform configuration syntax."""
    
    def score(
        self,
        generated: Any,
        expected: dict[str, Any] | None,
        metadata: dict[str, Any],
    ) -> Score:
        """Score Terraform config validity."""
        if isinstance(generated, str):
            # Basic HCL validation (simplified)
            is_valid = (
                "resource" in generated or
                "data" in generated or
                "module" in generated
            )
        else:
            is_valid = True
        
        return Score(
            name=self.name,
            value=is_valid,
            eval_id=self.eval_id,
            comment="Terraform config validation",
            metadata=metadata,
        )


class TerraformSecurityScorer(Scorer):
    """Checks Terraform security best practices (DevSecOps)."""
    
    def score(
        self,
        generated: Any,
        expected: dict[str, Any] | None,
        metadata: dict[str, Any],
    ) -> Score:
        """Score Terraform security practices."""
        if isinstance(generated, str):
            config_text = generated
        else:
            config_text = str(generated)
        
        security_score = 1.0
        issues = []
        
        # Check for hardcoded secrets
        if "password" in config_text.lower() and "=" in config_text:
            # Simple check - in real implementation, use regex/parsing
            if '"password"' in config_text or "'password'" in config_text:
                security_score -= 0.5
                issues.append("Potential hardcoded password")
        
        # Check for public access
        if "public_access" in config_text.lower():
            if "true" in config_text.lower():
                security_score -= 0.3
                issues.append("Public access enabled")
        
        # Check for encryption
        if "encryption" in config_text.lower():
            if "false" in config_text.lower():
                security_score -= 0.4
                issues.append("Encryption disabled")
        
        security_score = max(0.0, security_score)
        
        return Score(
            name=self.name,
            value=security_score,
            eval_id=self.eval_id,
            comment=f"Security score: {security_score:.2%}. Issues: {', '.join(issues) if issues else 'None'}",
            metadata={**metadata, "issues": issues},
        )


async def main():
    """Run Terraform evaluation example."""
    print("=== Terraform Configuration Evaluation ===\n")
    
    # Create dataset
    dataset = [
        DatasetItem(
            id="tf-1",
            input={
                "prompt": "Create an S3 bucket with encryption enabled",
                "entity_type": "aws_s3_bucket",
            },
            expected={"resource_type": "aws_s3_bucket"},
        ),
        DatasetItem(
            id="tf-2",
            input={
                "prompt": "Create an RDS instance with encryption",
                "entity_type": "aws_db_instance",
            },
            expected={"resource_type": "aws_db_instance"},
        ),
    ]
    
    # Create experiment with DevSecOps scorers
    experiment = Experiment(
        name="terraform_configuration",
        dataset=dataset,
        scorers=[
            TerraformValidScorer(name="tf_valid", eval_id="tf_valid.v1"),
            TerraformSecurityScorer(name="tf_security", eval_id="tf_security.v1"),
        ],
    )
    
    # Create adapter for DevOps agent
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        endpoint="/generate/terraform",
    )
    
    # Run experiment
    print("Running experiment...")
    result = await experiment.run(
        adapter=adapter,
        model="gpt-4",
    )
    
    # Print results
    print(f"\nExperiment completed: {result.run_id}")
    print(f"Total scores: {len(result.scores)}")
    print("\nScore summary:")
    for score in result.scores:
        print(f"  {score.name}: {score.value} - {score.comment}")


if __name__ == "__main__":
    asyncio.run(main())
