# Policy-as-Code

Guardrails defined as YAML/JSON. Version-controlled, testable, reusable.

## Structure

- **Metadata:** name, version, description.
- **Rules:** list of guardrail rules (id, type, enabled, threshold, action, config).

## Rule types

| Type | Description |
|------|-------------|
| toxicity | Toxic content |
| pii | PII entities |
| prompt_injection | Prompt injection |
| hallucination | Hallucinations (optional LLM) |
| keyword, regex, sensitive_data | Pattern/keyword checks |

## Example

```yaml
name: customer-support-guardrails
version: v1
rules:
  - id: block-toxicity
    type: toxicity
    enabled: true
    threshold: 0.7
    action: block
  - id: detect-pii
    type: pii
    enabled: true
    action: warn
```

Load with `aieval.policies.policy_loader.load_policy(path)` and run with `PolicyEngine`. See [guardrails](guardrails.md) and `examples/policies/`.
