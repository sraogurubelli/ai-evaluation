"""Simple evaluation example using JSONL dataset."""

import asyncio
from ai_evolution.core.experiment import Experiment
from ai_evolution.core.types import DatasetItem
from ai_evolution.datasets import load_jsonl_dataset
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.sinks.stdout import StdoutSink


# Simple adapter that just returns the input (for testing)
class SimpleAdapter:
    async def generate(self, input_data, model=None, **kwargs):
        # In real usage, this would call an AI system
        return input_data.get("prompt", "")


async def main():
    # Load dataset
    dataset = load_jsonl_dataset("examples/datasets/simple.jsonl")
    
    # Create scorers
    scorers = [
        DeepDiffScorer(version="v1"),
    ]
    
    # Create experiment
    experiment = Experiment(
        name="simple_eval",
        dataset=dataset,
        scorers=scorers,
    )
    
    # Create adapter
    adapter = SimpleAdapter()
    
    # Run experiment
    run = await experiment.run(adapter=adapter, concurrency_limit=1)
    
    # Output results
    sink = StdoutSink()
    sink.emit_run(run)
    sink.flush()


if __name__ == "__main__":
    asyncio.run(main())
