"""Example: Using AI Evolution SDK.

This example demonstrates how customers (internal or external) can use
the AI Evolution SDK to run evaluations.
"""

import asyncio
from ai_evolution import (
    # Core types
    DatasetItem,
    Experiment,
    # Adapters
    HTTPAdapter,
    # Scorers
    DeepDiffScorer,
    SchemaValidationScorer,
    # Dataset loaders
    load_jsonl_dataset,
    # Sinks
    StdoutSink,
    CSVSink,
    JSONSink,
    # Runner
    EvaluationRunner,
    run_evaluation,
)


async def example_basic_evaluation():
    """Basic evaluation using Experiment class."""
    print("=== Example 1: Basic Evaluation ===")
    
    # Load dataset
    dataset = load_jsonl_dataset("examples/datasets/sample.jsonl")
    
    # Create adapter
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        auth_token="your-token",
    )
    
    # Create scorers
    scorers = [
        DeepDiffScorer(
            name="deep_diff_v3",
            eval_id="deep_diff_v3.v1",
            version="v3",
        ),
        SchemaValidationScorer(),
    ]
    
    # Create experiment
    experiment = Experiment(
        name="my_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    # Run experiment
    result = await experiment.run(
        adapter=adapter,
        model="gpt-4o",
        concurrency_limit=5,
    )
    
    print(f"Experiment completed: {result.run_id}")
    print(f"Total scores: {len(result.scores)}")


async def example_runner_evaluation():
    """Evaluation using EvaluationRunner (ai-evals style)."""
    print("\n=== Example 2: Using EvaluationRunner ===")
    
    # Load dataset
    dataset = load_jsonl_dataset("examples/datasets/sample.jsonl")
    
    # Create adapter
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
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
    
    # Create sinks
    sinks = [
        StdoutSink(),
        CSVSink("results/evaluation.csv"),
        JSONSink("results/evaluation.json"),
    ]
    
    # Use runner
    runner = EvaluationRunner()
    result = await runner.run(
        dataset=dataset,
        adapter=adapter,
        scorers=scorers,
        model="gpt-4o",
        experiment_name="runner_example",
        sinks=sinks,
    )
    
    print(f"Evaluation completed: {result.run_id}")


async def example_registry_evaluation():
    """Evaluation using registry (ai-evals style)."""
    print("\n=== Example 3: Registry-Based Evaluation ===")
    
    # Load dataset (with outputs already populated)
    dataset = load_jsonl_dataset("examples/datasets/sample_with_outputs.jsonl")
    
    # Create adapter (for generating outputs if needed)
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
        auth_token="your-token",
    )
    
    # Create sinks
    sinks = [
        StdoutSink(),
        JSONSink("results/registry_eval.json"),
    ]
    
    # Use runner with registry
    runner = EvaluationRunner()
    scores = await runner.run_from_registry(
        registry_path="examples/evals/registry.yaml",
        eval_id="groundedness.v1",
        dataset=dataset,
        adapter=adapter,
        model="gpt-4o",
        agent_name="my-agent",
        agent_version="v1.0.0",
        env="local",
        sinks=sinks,
    )
    
    print(f"Evaluation completed: {len(scores)} scores generated")


async def example_convenience_function():
    """Using the convenience function."""
    print("\n=== Example 4: Convenience Function ===")
    
    from ai_evolution import run_evaluation
    
    # Load dataset
    dataset = load_jsonl_dataset("examples/datasets/sample.jsonl")
    
    # Create adapter
    adapter = HTTPAdapter(
        base_url="http://localhost:8000",
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
    
    # Run evaluation
    result = await run_evaluation(
        dataset=dataset,
        adapter=adapter,
        scorers=scorers,
        model="gpt-4o",
        experiment_name="convenience_example",
    )
    
    print(f"Evaluation completed: {result.run_id}")


async def example_custom_scorer():
    """Creating and using a custom scorer."""
    print("\n=== Example 5: Custom Scorer ===")
    
from ai_evolution import Scorer
from ai_evolution.core.types import Score, DatasetItem
from typing import Any
    
    class CustomScorer(Scorer):
        """Custom scorer that checks if output contains a keyword."""
        
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
            """Check if generated output contains keyword."""
            contains = self.keyword.lower() in generated.lower()
            
            return Score(
                name=self.name,
                value=float(contains),
                eval_id=self.eval_id,
                comment=f"Keyword '{self.keyword}' {'found' if contains else 'not found'}",
            )
    
    # Use custom scorer
    dataset = load_jsonl_dataset("examples/datasets/sample.jsonl")
    adapter = HTTPAdapter(base_url="http://localhost:8000")
    
    experiment = Experiment(
        name="custom_scorer_example",
        dataset=dataset,
        scorers=[CustomScorer(keyword="success")],
    )
    
    result = await experiment.run(adapter=adapter, model="gpt-4o")
    print(f"Custom scorer evaluation completed: {result.run_id}")


async def main():
    """Run all examples."""
    try:
        await example_basic_evaluation()
        await example_runner_evaluation()
        # await example_registry_evaluation()  # Requires registry.yaml
        await example_convenience_function()
        await example_custom_scorer()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
