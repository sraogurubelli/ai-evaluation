# Guardrails

Real-time safety checks for prompts and responses. Use in production or in offline evals.

## Features

- Policy-as-code (YAML/JSON). Types: toxicity, PII, prompt injection, hallucination, keyword, regex, sensitive data.
- Load policy, run validation, block/warn/log by rule.

## Quick start

1. Create a policy YAML (see [policy-as-code](policy-as-code.md) for structure).
2. Load and run:

```python
from aieval.policies.policy_loader import load_policy
from aieval.policies.policy_engine import PolicyEngine

policy = load_policy("policies/customer-support.yaml")
engine = PolicyEngine(policy)
result = engine.validate(prompt="...", response="...")
```

## Integration

- **API:** Use guardrail middleware or validators in your FastAPI app.
- **Experiments:** Use guardrail scorers in offline evaluations.

See [policy-as-code](policy-as-code.md) for rule types and config. Code: `src/aieval/scorers/guardrails/`, `src/aieval/policies/`.
