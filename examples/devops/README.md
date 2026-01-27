# DevOps Agent Evaluation Examples

This directory contains examples for evaluating DevOps and DevSecOps agents.

## Examples

- `kubernetes_eval.py` - Kubernetes config generation evaluation
- `terraform_eval.py` - Terraform configuration evaluation
- `dockerfile_eval.py` - Dockerfile generation evaluation
- `cicd_eval.py` - CI/CD pipeline generation evaluation

## Usage

```bash
# Run Kubernetes evaluation
python examples/devops/kubernetes_eval.py

# Run Terraform evaluation
python examples/devops/terraform_eval.py
```

## Creating Custom DevOps Scorers

See `docs/domain-abstraction.md` for guidance on creating domain-specific scorers.
