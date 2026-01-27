# AI Evolution SDK

The AI Evolution SDK provides a clean, customer-friendly interface for running evaluations, creating custom scorers, and integrating with AI systems.

## Installation

```bash
pip install ai-evolution
```

## Quick Start

### Basic Evaluation

```python
from ai_evolution import Experiment, HTTPAdapter, DeepDiffScorer, load_jsonl_dataset

# Load dataset
dataset = load_jsonl_dataset("dataset.jsonl")

# Create adapter
adapter = HTTPAdapter(
    base_url="http://your-api.com",
    auth_token="your-token",
)

# Create scorers
scorers = [
    DeepDiffScorer(
        name="deep_diff_v3",
        eval_id="deep_diff_v3.v1",
        version="v3",
    ),
]

# Create and run experiment
experiment = Experiment(
    name="my_evaluation",
    dataset=dataset,
    scorers=scorers,
)

result = await experiment.run(
    adapter=adapter,
    model="gpt-4o",
    concurrency_limit=5,
)

print(f"Evaluation completed: {result.run_id}")
print(f"Total scores: {len(result.scores)}")
```

### Using EvaluationRunner (ai-evals style)

```python
from ai_evolution import (
    EvaluationRunner,
    HTTPAdapter,
    DeepDiffScorer,
    load_jsonl_dataset,
    StdoutSink,
    CSVSink,
)

# Load dataset
dataset = load_jsonl_dataset("dataset.jsonl")

# Create adapter
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="token")

# Create scorers
scorers = [DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")]

# Create sinks
sinks = [
    StdoutSink(),
    CSVSink("results/evaluation.csv"),
]

# Use runner
runner = EvaluationRunner()
result = await runner.run(
    dataset=dataset,
    adapter=adapter,
    scorers=scorers,
    model="gpt-4o",
    experiment_name="my_eval",
    sinks=sinks,
)
```

### Registry-Based Evaluation (ai-evals style)

```python
from ai_evolution import EvaluationRunner, HTTPAdapter, load_jsonl_dataset

# Load dataset (with outputs already populated)
dataset = load_jsonl_dataset("dataset_with_outputs.jsonl")

# Create adapter (for generating outputs if needed)
adapter = HTTPAdapter(base_url="http://your-api.com", auth_token="token")

# Use runner with registry
runner = EvaluationRunner()
scores = await runner.run_from_registry(
    registry_path="evals/registry.yaml",
    eval_id="groundedness.v1",
    dataset=dataset,
    adapter=adapter,
    model="gpt-4o",
    agent_name="my-agent",
    agent_version="v1.0.0",
    env="local",
)
```

## Core Concepts

### Dataset

A dataset is a collection of test cases:

```python
from ai_evolution import DatasetItem

item = DatasetItem(
    id="test-001",
    input={"prompt": "What is 2+2?"},
    expected={"contains": "4"},
)
```

### Adapters

Adapters connect to AI systems:

```python
from ai_evolution import HTTPAdapter, MLInfraAdapter

# Generic HTTP adapter (recommended)
adapter = HTTPAdapter(
    base_url="http://your-api.com",
    auth_token="token",
    context_field_name="context",
    context_data={"account_id": "123"},
)

# ML Infra adapter (backward compatibility)
adapter = MLInfraAdapter(
    base_url="http://ml-infra-server.com",
    auth_token="token",
    account_id="account-123",
    org_id="org-456",
    project_id="project-789",
)
```

### Scorers

Scorers evaluate outputs:

```python
from ai_evolution import DeepDiffScorer, SchemaValidationScorer

# DeepDiff scorer
scorer = DeepDiffScorer(
    name="deep_diff_v3",
    eval_id="deep_diff_v3.v1",
    version="v3",
)

# Schema validation scorer
scorer = SchemaValidationScorer()
```

### Custom Scorers

Create your own scorer:

```python
from ai_evolution import Scorer
from ai_evolution.core.types import Score, DatasetItem
from typing import Any

class CustomScorer(Scorer):
    def __init__(self, keyword: str):
        self.keyword = keyword
        super().__init__(
            name="contains_keyword",
            eval_id="contains_keyword.v1",
        )
    
    async def score(
        self,
        item: DatasetItem,
        generated: str,
        expected: str | None = None,
        **kwargs: Any,
    ) -> Score:
        contains = self.keyword.lower() in generated.lower()
        return Score(
            name=self.name,
            value=float(contains),
            eval_id=self.eval_id,
            comment=f"Keyword '{self.keyword}' {'found' if contains else 'not found'}",
        )
```

### Sinks

Sinks handle output:

```python
from ai_evolution import StdoutSink, CSVSink, JSONSink, LangfuseSink

sinks = [
    StdoutSink(),                    # Console output
    CSVSink("results/eval.csv"),     # CSV file
    JSONSink("results/eval.json"),   # JSON file
    LangfuseSink(),                  # Langfuse (if configured)
]
```

## Registry System

The registry allows you to define evaluations declaratively:

**registry.yaml:**
```yaml
- eval_id: groundedness.v1
  score_name: groundedness
  evaluator: evaluators/groundedness.py
  environments: [local, ci, prod]
  owner: platform-team
  description: "Check if answer is grounded in context"
```

**evaluators/groundedness.py:**
```python
from ai_evolution.core.types import Score
from typing import Any

def evaluate(
    input: dict[str, Any],
    output: Any,
    expected: dict[str, Any] | None,
    eval_id: str,
    agent_name: str,
    agent_version: str,
    env: str,
) -> list[Score]:
    # Your evaluation logic
    is_grounded = check_groundedness(output, input.get("context", ""))
    
    return [
        Score(
            score_name="groundedness",
            value=float(is_grounded),
            eval_id=eval_id,
            agent_name=agent_name,
            agent_version=agent_version,
            env=env,
            comment="Answer is grounded in context" if is_grounded else "Not grounded",
        )
    ]
```

## Examples

See `examples/sdk_example.py` for complete examples.

## API Reference

### Core Types

- `DatasetItem`: Single test case
- `Score`: Evaluation result
- `ExperimentRun`: Complete experiment execution

### Experiment System

- `Experiment`: Main experiment orchestrator
- `EvaluationRunner`: Runner for executing evaluations
- `run_evaluation()`: Convenience function

### Adapters

- `HTTPAdapter`: Generic HTTP/REST adapter
- `MLInfraAdapter`: ML Infra compatibility adapter
- `LangfuseAdapter`: Langfuse adapter

### Scorers

- `DeepDiffScorer`: DeepDiff-based comparison
- `SchemaValidationScorer`: JSON schema validation
- `DashboardQualityScorer`: Dashboard quality checks
- `KnowledgeGraphQualityScorer`: Knowledge graph quality

### Dataset Loaders

- `load_jsonl_dataset()`: Load JSONL dataset
- `load_index_csv_dataset()`: Load index CSV dataset
- `FunctionDataset`: Function-based dataset

### Sinks

- `StdoutSink`: Console output
- `CSVSink`: CSV file output
- `JSONSink`: JSON file output
- `LangfuseSink`: Langfuse integration

## Task Abstraction (Braintrust-style)

Tasks provide a clean abstraction for what you're evaluating:

```python
from ai_evolution import FunctionTask, AdapterTask, HTTPAdapter

# Define task as a function
async def my_llm_call(input: dict[str, Any]) -> str:
    return await llm.generate(input["prompt"])

task = FunctionTask(my_llm_call)
output = await task.run({"prompt": "Hello"})

# Or use adapter as task
adapter = HTTPAdapter(base_url="http://api.com")
task = AdapterTask(adapter, model="gpt-4o")
output = await task.run({"prompt": "Hello"})
```

## Assertion System (OpenAI Evals style)

Assertions provide granular checks that can be combined:

```python
from ai_evolution import (
    ContainsAssertion,
    RegexAssertion,
    JSONSchemaAssertion,
    AssertionScorer,
)

# Create assertions
assertions = [
    ContainsAssertion("success"),
    RegexAssertion(r"\d+"),
    JSONSchemaAssertion({"type": "object"}),
]

# Combine into scorer
scorer = AssertionScorer(
    name="quality_check",
    eval_id="quality_check.v1",
    assertions=assertions,
    require_all=True,  # All must pass
)

# Score output
result = scorer.score('{"status": "success", "code": 200}')
```

## Experiment Comparison (Braintrust-style)

Compare runs to detect improvements and regressions:

```python
from ai_evolution import compare_runs, get_regressions

# Compare two runs
comparison = compare_runs(baseline_run, new_run)

print(f"Improvements: {comparison.improvements}")
print(f"Regressions: {comparison.regressions}")

# Check for regressions (useful for CI/CD)
regressions = get_regressions(comparison)
if regressions:
    raise Exception(f"Regressions found: {regressions}")
```

## Autoevals-Style Scorers (Braintrust)

AI Evolution includes pre-built scorers inspired by Braintrust's autoevals library:

### LLM-as-Judge Scorers

```python
from ai_evolution import FactualityScorer, HelpfulnessScorer, RAGRelevanceScorer

# Factuality: Checks if output is factually correct
scorer = FactualityScorer(model="gpt-4o-mini")
score = scorer.score(
    generated="Paris is the capital of France.",
    expected="Paris is the capital of France.",
    metadata={"input": {"prompt": "What is the capital of France?"}},
)

# Helpfulness: Evaluates how helpful the output is
scorer = HelpfulnessScorer()
score = scorer.score(
    generated="To reset password, go to Settings > Security.",
    expected="Helpful",
    metadata={"input": {"prompt": "How do I reset my password?"}},
)

# RAG Relevance: Checks if output is relevant to retrieved context
scorer = RAGRelevanceScorer()
score = scorer.score(
    generated="Based on the document, the answer is 42.",
    expected="Relevant",
    metadata={"input": {"context": "The document states..."}},
)
```

### Heuristic Scorers

```python
from ai_evolution import LevenshteinScorer

# Levenshtein: String similarity using edit distance
scorer = LevenshteinScorer(normalize=True)
score = scorer.score(
    generated="Hello world",
    expected="Hello world!",
    metadata={},
)
```

### Statistical Scorers

```python
from ai_evolution import BLUEScorer

# BLEU: N-gram overlap score
scorer = BLUEScorer(n=4)
score = scorer.score(
    generated="The cat sat on the mat",
    expected="A cat sat on a mat",
    metadata={},
)
```

### Embedding-Based Scorers

```python
from ai_evolution import EmbeddingSimilarityScorer

# Embedding Similarity: Semantic similarity using embeddings
scorer = EmbeddingSimilarityScorer(model="text-embedding-3-small")
score = scorer.score(
    generated="The weather is nice today",
    expected="It's a beautiful day outside",
    metadata={},
)
```

**Note**: Some scorers require additional dependencies:
- LLM scorers: `pip install openai`
- BLEU scorer: `pip install nltk`
- Levenshtein scorer: `pip install python-Levenshtein` or `pip install rapidfuzz`
- Embedding scorer: `pip install openai numpy`

## Best Practices

1. **Use HTTPAdapter for new integrations**: It's generic and configurable
2. **Use Task abstraction**: Clean separation between what you're evaluating and how
3. **Use assertions for granular checks**: Combine multiple assertions into scorers
4. **Compare runs regularly**: Detect regressions early with comparison
5. **Create custom scorers**: Extend the `Scorer` base class for domain-specific evaluation
6. **Use sinks for output**: Multiple sinks allow output to multiple destinations
7. **Use registry for declarative evals**: Makes evals easier to manage and version
8. **Track agent versions**: Always provide `agent_name` and `agent_version` for regression tracking

## Migration from ai-evals

If you're using ai-evals, the SDK provides compatibility:

```python
# ai-evals style
from ai_evolution import EvaluationRunner, load_jsonl_dataset

runner = EvaluationRunner()
scores = await runner.run_from_registry(
    registry_path="registry.yaml",
    eval_id="groundedness.v1",
    dataset=load_jsonl_dataset("dataset.jsonl"),
    adapter=HTTPAdapter(...),
    agent_name="my-agent",
    agent_version="v1.0",
    env="ci",
)
```

## Support

For questions or issues, please open an issue on GitHub.
