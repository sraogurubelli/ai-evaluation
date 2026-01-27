"""Example: Using Temporal workflows for experiment execution."""

import asyncio
from ai_evolution.workflows.client import (
    start_experiment_workflow,
    get_workflow_status,
    get_workflow_result,
)


async def main():
    """Example of running an experiment with Temporal."""
    print("=== Temporal Experiment Execution ===\n")
    
    # Experiment configuration
    config = {
        "dataset": {
            "type": "jsonl",
            "path": "datasets/sample.jsonl",
        },
        "adapter": {
            "type": "http",
            "base_url": "http://localhost:8000",
        },
        "scorers": [
            {"type": "deep_diff", "version": "v3"},
        ],
        "models": ["gpt-4"],
        "execution": {
            "concurrency_limit": 5,
        },
        "sinks": [
            {"type": "csv", "path": "results/temporal_results.csv"},
        ],
    }
    
    # Start workflow
    print("Starting experiment workflow...")
    workflow_id = await start_experiment_workflow(
        experiment_name="temporal_example",
        config=config,
    )
    
    print(f"Workflow started: {workflow_id}")
    
    # Poll for status
    print("\nPolling workflow status...")
    while True:
        status = await get_workflow_status(workflow_id)
        print(f"Status: {status['status']}")
        
        if status["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            break
        
        await asyncio.sleep(2)
    
    # Get result
    if status["status"] == "COMPLETED":
        print("\nWorkflow completed! Getting result...")
        result = await get_workflow_result(workflow_id)
        print(f"Experiment run ID: {result.get('run_id')}")
        print(f"Total scores: {len(result.get('scores', []))}")
    else:
        print(f"\nWorkflow {status['status']}")


if __name__ == "__main__":
    asyncio.run(main())
