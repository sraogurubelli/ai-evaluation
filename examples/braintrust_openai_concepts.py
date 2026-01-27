"""Examples: Braintrust and OpenAI Evals concepts.

This demonstrates how to use:
1. Task abstraction (Braintrust-style)
2. Assertion system (OpenAI Evals style)
3. Experiment comparison (Braintrust-style)
"""

import asyncio
from ai_evolution import (
    # Core
    Experiment,
    DatasetItem,
    # Task abstraction
    Task,
    FunctionTask,
    AdapterTask,
    # Assertions
    ContainsAssertion,
    RegexAssertion,
    JSONSchemaAssertion,
    AssertionScorer,
    # Comparison
    compare_runs,
    get_regressions,
    # Adapters
    HTTPAdapter,
    # Dataset loaders
    load_jsonl_dataset,
)


# Example 1: Task Abstraction (Braintrust-style)
async def example_task_abstraction():
    """Using Task abstraction for clean evaluation."""
    print("=== Example 1: Task Abstraction ===")
    
    # Define your task as a simple function
    async def my_llm_task(input: dict[str, Any]) -> str:
        """Your LLM call or agent logic."""
        # In real usage, this would call your LLM/agent
        prompt = input.get("prompt", "")
        return f"Response to: {prompt}"
    
    # Create task
    task = FunctionTask(my_llm_task)
    
    # Or use adapter as task
    adapter = HTTPAdapter(base_url="http://api.com")
    adapter_task = AdapterTask(adapter, model="gpt-4o")
    
    # Run task
    output = await task.run({"prompt": "Hello"})
    print(f"Task output: {output}")


# Example 2: Assertion System (OpenAI Evals style)
async def example_assertions():
    """Using assertions for granular checks."""
    print("\n=== Example 2: Assertion System ===")
    
    # Create assertions
    assertions = [
        ContainsAssertion("success", case_sensitive=False),
        RegexAssertion(r"\d+"),  # Must contain a number
        JSONSchemaAssertion({
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "code": {"type": "number"},
            },
            "required": ["status"],
        }),
    ]
    
    # Create assertion scorer
    scorer = AssertionScorer(
        name="quality_check",
        eval_id="quality_check.v1",
        assertions=assertions,
        require_all=True,  # All assertions must pass
    )
    
    # Score outputs
    output1 = '{"status": "success", "code": 200}'
    result1 = scorer.score(output1)
    print(f"Output 1 passed: {result1['value'] == 1.0}")
    
    output2 = "failure"
    result2 = scorer.score(output2)
    print(f"Output 2 passed: {result2['value'] == 1.0}")


# Example 3: Experiment Comparison (Braintrust-style)
async def example_comparison():
    """Comparing experiment runs to detect regressions."""
    print("\n=== Example 3: Experiment Comparison ===")
    
    # Load dataset
    dataset = load_jsonl_dataset("examples/datasets/sample.jsonl")
    
    # Create adapter
    adapter = HTTPAdapter(base_url="http://api.com")
    
    # Run baseline experiment
    baseline_experiment = Experiment(
        name="baseline",
        dataset=dataset,
        scorers=[...],  # Your scorers
    )
    baseline_run = await baseline_experiment.run(adapter=adapter, model="gpt-4o")
    
    # Run new experiment (maybe with different model/prompt)
    new_experiment = Experiment(
        name="new_version",
        dataset=dataset,
        scorers=[...],  # Same scorers
    )
    new_run = await new_experiment.run(adapter=adapter, model="gpt-4o-turbo")
    
    # Compare runs
    comparison = compare_runs(baseline_run, new_run, dataset=dataset)
    
    print(f"Improvements: {comparison.improvements}")
    print(f"Regressions: {comparison.regressions}")
    print(f"Unchanged: {comparison.unchanged}")
    
    # Check for regressions (useful for CI/CD)
    regressions = get_regressions(comparison, min_regressions=1)
    if regressions:
        print(f"⚠️  Regressions detected: {regressions}")
        # In CI/CD, you might want to fail the build
        # raise Exception(f"Regressions found: {regressions}")


# Example 4: Combining Task + Assertions
async def example_task_with_assertions():
    """Using Task abstraction with assertion-based scoring."""
    print("\n=== Example 4: Task + Assertions ===")
    
    # Define task
    async def my_task(input: dict[str, Any]) -> str:
        return f"Response: {input.get('prompt', '')}"
    
    task = FunctionTask(my_task)
    
    # Create assertion scorer
    scorer = AssertionScorer(
        name="response_quality",
        eval_id="response_quality.v1",
        assertions=[
            ContainsAssertion("Response:"),
            RegexAssertion(r"Response: .+"),
        ],
    )
    
    # Run task and score
    output = await task.run({"prompt": "Hello"})
    result = scorer.score(output)
    print(f"Task output: {output}")
    print(f"Score: {result['value']}, Comment: {result['comment']}")


async def main():
    """Run all examples."""
    try:
        await example_task_abstraction()
        await example_assertions()
        # await example_comparison()  # Requires actual runs
        await example_task_with_assertions()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    from typing import Any
    asyncio.run(main())
