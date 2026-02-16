"""Utilities for CI/CD integration."""

import json
from pathlib import Path
from typing import Any

from aieval.core.types import EvalResult
from aieval.ci.gates import DeploymentGate
from aieval.agents.tools.baseline_tools import BaselineManager


def load_run_from_json(path: str | Path) -> EvalResult:
    """
    Load Run object from JSON file.

    Args:
        path: Path to JSON file containing run data

    Returns:
        Run object
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Run file not found: {path}")

    with path.open("r") as f:
        data = json.load(f)

    # Convert to Run object
    from aieval.core.types import Score
    from datetime import datetime

    return EvalResult(
        eval_id=data.get("eval_id", "unknown"),
        run_id=data.get("run_id", "unknown"),
        dataset_id=data.get("dataset_id", "unknown"),
        scores=[Score(**s) for s in data.get("scores", [])],
        metadata=data.get("metadata", {}),
        created_at=datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("created_at"), str)
        else data.get("created_at"),
    )


def compare_runs(current_run: EvalResult, baseline_run: EvalResult) -> dict[str, Any]:
    """
    Compare two runs and detect regressions.

    Args:
        current_run: Current run to check
        baseline_run: Baseline run to compare against

    Returns:
        Dictionary with comparison results:
        - regressions: list of regression details
        - improvements: list of improvement details
        - score_changes: dict of score_name -> change
    """
    # Group scores by dataset item ID
    current_scores_by_item = {}
    baseline_scores_by_item = {}

    for score in current_run.scores:
        item_id = score.metadata.get("item_id") or score.metadata.get("test_id") or "unknown"
        if item_id not in current_scores_by_item:
            current_scores_by_item[item_id] = {}
        current_scores_by_item[item_id][score.name] = score

    for score in baseline_run.scores:
        item_id = score.metadata.get("item_id") or score.metadata.get("test_id") or "unknown"
        if item_id not in baseline_scores_by_item:
            baseline_scores_by_item[item_id] = {}
        baseline_scores_by_item[item_id][score.name] = score

    regressions = []
    improvements = []
    score_changes = {}

    # Compare scores
    all_item_ids = set(current_scores_by_item.keys()) | set(baseline_scores_by_item.keys())

    for item_id in all_item_ids:
        current_item_scores = current_scores_by_item.get(item_id, {})
        baseline_item_scores = baseline_scores_by_item.get(item_id, {})

        # Compare each score
        all_score_names = set(current_item_scores.keys()) | set(baseline_item_scores.keys())

        for score_name in all_score_names:
            current_score = current_item_scores.get(score_name)
            baseline_score = baseline_item_scores.get(score_name)

            if current_score is None or baseline_score is None:
                continue

            current_value = _normalize_score_value(current_score.value)
            baseline_value = _normalize_score_value(baseline_score.value)

            change = current_value - baseline_value

            # Track overall change
            if score_name not in score_changes:
                score_changes[score_name] = {
                    "total_change": 0.0,
                    "item_count": 0,
                }
            score_changes[score_name]["total_change"] += change
            score_changes[score_name]["item_count"] += 1

            # Detect regression (threshold: 0.01)
            if change < -0.01:
                regressions.append(
                    {
                        "item_id": item_id,
                        "score_name": score_name,
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change": change,
                    }
                )
            elif change > 0.01:
                improvements.append(
                    {
                        "item_id": item_id,
                        "score_name": score_name,
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change": change,
                    }
                )

    # Calculate average changes
    for score_name, change_data in score_changes.items():
        if change_data["item_count"] > 0:
            change_data["average_change"] = change_data["total_change"] / change_data["item_count"]

    return {
        "regressions": regressions,
        "improvements": improvements,
        "score_changes": score_changes,
    }


def _normalize_score_value(value: Any) -> float:
    """Normalize score value to float."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        return float(value)
    else:
        return 0.0


def check_deployment_gate(
    run_path: str | Path,
    baseline_run_path: str | Path | None = None,
    score_thresholds: dict[str, float] | None = None,
    max_regressions: int = 0,
) -> dict[str, Any]:
    """
    Check deployment gate for a run.

    Args:
        run_path: Path to current run JSON file
        baseline_run_path: Optional path to baseline run JSON file
        score_thresholds: Dictionary of score_name -> minimum_value
        max_regressions: Maximum number of regressions allowed

    Returns:
        Dictionary with gate check results
    """
    current_result = load_run_from_json(run_path)
    baseline_result = None

    if baseline_run_path:
        baseline_result = load_run_from_json(baseline_run_path)

    gate = DeploymentGate(
        score_thresholds=score_thresholds,
        max_regressions=max_regressions,
    )

    check_result = gate.check(current_result, baseline_result)

    return check_result
