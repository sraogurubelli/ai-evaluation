"""Evaluation runner for executing evaluations.

The runner provides a clean interface for running evaluations, similar to ai-evals.
It supports both programmatic and registry-based evaluation execution.
"""

import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable

from ai_evolution.core.experiment import Experiment
from ai_evolution.core.types import DatasetItem, Score
from ai_evolution.adapters.base import Adapter
from ai_evolution.sinks.base import Sink
from ai_evolution.sinks.stdout import StdoutSink

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Runner for executing evaluations.
    
    Similar to ai-evals runner, but adapted for ai-evolution's architecture.
    Supports both:
    1. Direct evaluation (using Experiment class)
    2. Registry-based evaluation (loading evaluators dynamically)
    
    Example:
        runner = EvaluationRunner()
        result = await runner.run(
            dataset=load_dataset("dataset.jsonl"),
            adapter=HTTPAdapter(...),
            scorers=[DeepDiffScorer(...)],
            model="gpt-4o"
        )
    """
    
    def __init__(self):
        """Initialize the evaluation runner."""
        self.logger = logging.getLogger(__name__)
    
    async def run(
        self,
        dataset: list[DatasetItem],
        adapter: Adapter,
        scorers: list[Any] | None = None,
        model: str | None = None,
        experiment_name: str = "evaluation",
        concurrency_limit: int = 5,
        sinks: list[Sink] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Run an evaluation.
        
        Args:
            dataset: List of dataset items to evaluate
            adapter: Adapter for generating outputs
            scorers: List of scorers to apply (if None, uses registry-based evaluation)
            model: Optional model name
            experiment_name: Name for the experiment
            concurrency_limit: Maximum concurrent evaluations
            sinks: List of sinks for output (defaults to StdoutSink)
            **kwargs: Additional arguments passed to adapter/scorers
        
        Returns:
            ExperimentRun result
        """
        sinks = sinks or [StdoutSink()]
        
        # Create experiment
        if scorers is None:
            raise ValueError("scorers must be provided for direct evaluation")
        
        experiment = Experiment(
            name=experiment_name,
            dataset=dataset,
            scorers=scorers,
        )
        
        # Run experiment
        run_result = await experiment.run(
            adapter=adapter,
            model=model,
            concurrency_limit=concurrency_limit,
            **kwargs,
        )
        
        # Emit to sinks
        for sink in sinks:
            sink.emit_run(run_result)
            sink.flush()
        
        return run_result
    
    async def run_from_registry(
        self,
        registry_path: str | Path,
        eval_id: str,
        dataset: list[DatasetItem],
        adapter: Adapter,
        model: str | None = None,
        agent_name: str = "unknown",
        agent_version: str = "unknown",
        env: str = "local",
        sinks: list[Sink] | None = None,
        **kwargs: Any,
    ) -> list[Score]:
        """
        Run evaluation from registry (ai-evals style).
        
        This loads an evaluator dynamically from the registry and runs it.
        
        Args:
            registry_path: Path to registry.yaml
            eval_id: ID of the eval to run (e.g., "groundedness.v1")
            dataset: List of dataset items (must have output populated)
            adapter: Adapter for generating outputs (if outputs not present)
            model: Optional model name
            agent_name: Name of the agent being evaluated
            agent_version: Version/commit of the agent
            env: Environment (e.g., 'local', 'ci', 'prod')
            sinks: List of sinks for output
            **kwargs: Additional arguments
        
        Returns:
            List of scores produced
        """
        from ai_evolution.sdk.registry import load_registry
        
        registry_path = Path(registry_path)
        sinks = sinks or [StdoutSink()]
        
        # Load registry and find eval
        registry = load_registry(registry_path)
        entry = next((e for e in registry if e.eval_id == eval_id), None)
        if entry is None:
            available = [e.eval_id for e in registry]
            raise ValueError(f"Eval '{eval_id}' not found. Available: {available}")
        
        # Check environment compatibility
        if entry.environments and env not in entry.environments:
            raise ValueError(
                f"Eval '{eval_id}' not configured for environment '{env}'. "
                f"Supported: {entry.environments}"
            )
        
        # Load evaluator
        evaluate_fn = self._load_evaluator(registry_path, entry.evaluator)
        
        # Check if outputs need to be generated
        items_without_output = [item for item in dataset if item.output is None]
        if items_without_output:
            self.logger.info(f"Generating outputs for {len(items_without_output)} items")
            # Generate outputs using adapter
            for item in items_without_output:
                try:
                    item.output = await adapter.generate(
                        input_data=item.input,
                        model=model,
                        **kwargs,
                    )
                except Exception as e:
                    self.logger.error(f"Failed to generate output for item {item.id}: {e}")
                    raise
        
        # Run evaluation
        all_scores: list[Score] = []
        for item in dataset:
            # Call evaluator with input/output/expected
            scores = evaluate_fn(
                input=item.input,
                output=item.output,
                expected=item.expected,
                eval_id=eval_id,
                agent_name=agent_name,
                agent_version=agent_version,
                env=env,
            )
            
            # Emit scores
            for score in scores:
                # Convert ai-evals Score format to ai-evolution Score format if needed
                if hasattr(score, "score_name"):
                    # ai-evals format: convert to ai-evolution format
                    from ai_evolution.core.types import Score as EvolutionScore
                    evolution_score = EvolutionScore(
                        name=score.score_name,
                        value=score.value,
                        eval_id=score.eval_id,
                        comment=score.comment,
                        metadata=score.metadata.copy(),
                        trace_id=score.trace_id,
                        observation_id=score.observation_id,
                    )
                    score = evolution_score
                
                # Enrich with dataset_item_id if not already in metadata
                if "dataset_item_id" not in score.metadata:
                    score.metadata["dataset_item_id"] = item.id
                
                all_scores.append(score)
                for sink in sinks:
                    sink.emit(score)
        
        # Flush all sinks
        for sink in sinks:
            sink.flush()
        
        return all_scores
    
    def _load_evaluator(self, registry_path: Path, evaluator_path: str) -> Callable:
        """
        Dynamically load an evaluator module.
        
        Args:
            registry_path: Path to registry.yaml (used to resolve relative paths)
            evaluator_path: Relative path to evaluator module
        
        Returns:
            The evaluate function from the module
        
        Raises:
            ValueError: If evaluator cannot be loaded or doesn't have evaluate function
        """
        full_path = registry_path.parent / evaluator_path
        
        spec = importlib.util.spec_from_file_location("evaluator", full_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load evaluator from {full_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, "evaluate"):
            raise ValueError(f"Evaluator {full_path} must have an 'evaluate' function")
        
        return module.evaluate


async def run_evaluation(
    dataset: list[DatasetItem],
    adapter: Adapter,
    scorers: list[Any],
    model: str | None = None,
    experiment_name: str = "evaluation",
    **kwargs: Any,
) -> Any:
    """
    Convenience function for running an evaluation.
    
    Example:
        result = await run_evaluation(
            dataset=load_dataset("dataset.jsonl"),
            adapter=HTTPAdapter(...),
            scorers=[DeepDiffScorer(...)],
            model="gpt-4o"
        )
    
    Args:
        dataset: List of dataset items
        adapter: Adapter for generating outputs
        scorers: List of scorers to apply
        model: Optional model name
        experiment_name: Name for the experiment
        **kwargs: Additional arguments
    
    Returns:
        ExperimentRun result
    """
    runner = EvaluationRunner()
    return await runner.run(
        dataset=dataset,
        adapter=adapter,
        scorers=scorers,
        model=model,
        experiment_name=experiment_name,
        **kwargs,
    )
