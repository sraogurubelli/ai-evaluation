"""Agent-agnostic SDK helpers for unit testing and single-item evaluation.

This module provides generic helpers that work with any adapter and scorer.
Consumer-specific helpers (e.g. DevOps index.csv, run_devops_eval) belong
in consumer samples (e.g. samples_sdk/consumers/devops).
"""

from typing import Any

from aieval.core.eval import Eval
from aieval.core.types import DatasetItem, Run, Score
from aieval.adapters.base import Adapter
from aieval.scorers.base import Scorer


def assert_score_min(
    result: Run,
    min_value: float,
    score_name: str | None = None,
) -> None:
    """
    Raise AssertionError if the (first or named) score is below the threshold.

    Purely generic; keeps assertions in the caller's control.

    Args:
        result: Run from eval.run() or run_single_item()
        min_value: Minimum acceptable score value (inclusive).
        score_name: If set, use the score with this name; otherwise use the first score.

    Raises:
        AssertionError: If no scores, or the selected score value < min_value.

    Example:
        result = await run_single_item(item, adapter, scorer, model="gpt-4o")
        assert_score_min(result, min_value=0.9)
        assert_score_min(result, min_value=0.8, score_name="deep_diff_v3")
    """
    if not result.scores:
        raise AssertionError(f"Run has no scores (min_value={min_value})")
    if score_name is not None:
        for s in result.scores:
            if s.name == score_name:
                if s.value < min_value:
                    raise AssertionError(
                        f"Score {score_name!r} = {s.value} below min_value {min_value}"
                    )
                return
        raise AssertionError(f"No score named {score_name!r} in result")
    score = result.scores[0]
    if score.value < min_value:
        raise AssertionError(
            f"Score {score.name!r} = {score.value} below min_value {min_value}"
        )


def score_single_output(
    generated: Any,
    expected: Any,
    scorer: Scorer,
    metadata: dict[str, Any] | None = None,
) -> Score:
    """
    Score a single output without running an experiment (convenience for unit tests).

    Args:
        generated: Generated output (YAML string, dict, etc.)
        expected: Expected output (YAML string, dict, etc.)
        scorer: Scorer instance to use
        metadata: Additional metadata (optional)

    Returns:
        Score object

    Example:
        from aieval import DeepDiffScorer
        scorer = DeepDiffScorer(version="v3")
        score = score_single_output(
            generated=generated_yaml,
            expected=expected_yaml,
            scorer=scorer,
            metadata={"test_id": "pipeline_create_001"},
        )
    """
    if metadata is None:
        metadata = {}
    return scorer.score(
        generated=generated,
        expected=expected,
        metadata=metadata,
    )


async def run_single_item(
    dataset_item: DatasetItem,
    adapter: Adapter,
    scorer: Scorer,
    model: str | None = None,
    concurrency_limit: int = 1,
    **kwargs: Any,
) -> Run:
    """
    Run a single dataset item end-to-end (convenience for unit/integration tests).

    Builds Experiment(name=..., dataset=[item], scorers=[scorer]) and runs it.
    Works with any Adapter and Scorer; agent-agnostic.

    Args:
        dataset_item: Single item to run
        adapter: Adapter instance (HTTP, SSE, Langfuse, etc.)
        scorer: Scorer instance
        model: Model name (optional)
        concurrency_limit: Max concurrent calls (default 1 for single item)
        **kwargs: Passed through to eval.run()

    Returns:
        Run result

    Example:
        from aieval import HTTPAdapter, DeepDiffScorer
        adapter = HTTPAdapter(base_url="http://localhost:8000")
        scorer = DeepDiffScorer(version="v3")
        result = await run_single_item(
            dataset_item=test_case,
            adapter=adapter,
            scorer=scorer,
            model="claude-3-7-sonnet",
        )
    """
    eval_ = Eval(
        name=f"unit_test_{dataset_item.id}",
        dataset=[dataset_item],
        scorers=[scorer],
    )
    return await eval_.run(
        adapter=adapter,
        model=model,
        concurrency_limit=concurrency_limit,
        **kwargs,
    )
