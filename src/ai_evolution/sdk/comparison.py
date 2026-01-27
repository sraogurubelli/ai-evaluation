"""Experiment comparison and diffing (Braintrust-style).

Provides side-by-side comparison of experiment runs with regression detection.
"""

from typing import Any
from dataclasses import dataclass, field
from ai_evolution.core.types import ExperimentRun, Score, DatasetItem


@dataclass
class RunComparison:
    """Comparison result between two experiment runs."""
    
    run1_id: str
    run2_id: str
    run1_scores: dict[str, list[float]]  # score_name -> list of values
    run2_scores: dict[str, list[float]]
    improvements: dict[str, int] = field(default_factory=dict)  # score_name -> count improved
    regressions: dict[str, int] = field(default_factory=dict)  # score_name -> count regressed
    unchanged: dict[str, int] = field(default_factory=dict)  # score_name -> count unchanged
    item_level_changes: list[dict[str, Any]] = field(default_factory=list)  # Per-item changes
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of comparison."""
        return {
            "run1_id": self.run1_id,
            "run2_id": self.run2_id,
            "improvements": self.improvements,
            "regressions": self.regressions,
            "unchanged": self.unchanged,
            "total_items": len(self.item_level_changes),
        }


def compare_runs(
    run1: ExperimentRun,
    run2: ExperimentRun,
    dataset: list[DatasetItem] | None = None,
    threshold: float = 0.01,
) -> RunComparison:
    """
    Compare two experiment runs and detect improvements/regressions.
    
    Similar to Braintrust's experiment comparison, this provides:
    - Side-by-side score comparison
    - Regression detection
    - Per-item change tracking
    
    Args:
        run1: First experiment run (baseline)
        run2: Second experiment run (to compare)
        dataset: Optional dataset items for per-item comparison
        threshold: Minimum change to consider significant (default: 0.01)
    
    Returns:
        RunComparison with detailed comparison results
    
    Example:
        comparison = compare_runs(baseline_run, new_run)
        print(f"Improvements: {comparison.improvements}")
        print(f"Regressions: {comparison.regressions}")
    """
    # Group scores by name and dataset item
    run1_scores_by_item: dict[str, dict[str, float]] = {}  # item_id -> score_name -> value
    run2_scores_by_item: dict[str, dict[str, float]] = {}
    
    for score in run1.scores:
        item_id = score.metadata.get("dataset_item_id", "unknown")
        if item_id not in run1_scores_by_item:
            run1_scores_by_item[item_id] = {}
        val = score.value
        if isinstance(val, bool):
            val = float(val)
        run1_scores_by_item[item_id][score.name] = val
    
    for score in run2.scores:
        item_id = score.metadata.get("dataset_item_id", "unknown")
        if item_id not in run2_scores_by_item:
            run2_scores_by_item[item_id] = {}
        val = score.value
        if isinstance(val, bool):
            val = float(val)
        run2_scores_by_item[item_id][score.name] = val
    
    # Aggregate scores by name
    run1_scores: dict[str, list[float]] = {}
    run2_scores: dict[str, list[float]] = {}
    
    for item_scores in run1_scores_by_item.values():
        for score_name, value in item_scores.items():
            if score_name not in run1_scores:
                run1_scores[score_name] = []
            run1_scores[score_name].append(value)
    
    for item_scores in run2_scores_by_item.values():
        for score_name, value in item_scores.items():
            if score_name not in run2_scores:
                run2_scores[score_name] = []
            run2_scores[score_name].append(value)
    
    # Calculate improvements/regressions
    improvements: dict[str, int] = {}
    regressions: dict[str, int] = {}
    unchanged: dict[str, int] = {}
    item_level_changes: list[dict[str, Any]] = []
    
    # Get all score names
    all_score_names = set(run1_scores.keys()) | set(run2_scores.keys())
    
    for score_name in all_score_names:
        improvements[score_name] = 0
        regressions[score_name] = 0
        unchanged[score_name] = 0
        
        # Get items that exist in both runs
        common_items = set(run1_scores_by_item.keys()) & set(run2_scores_by_item.keys())
        
        for item_id in common_items:
            score1 = run1_scores_by_item[item_id].get(score_name)
            score2 = run2_scores_by_item[item_id].get(score_name)
            
            if score1 is None or score2 is None:
                continue
            
            change = score2 - score1
            
            if abs(change) < threshold:
                unchanged[score_name] += 1
                change_type = "unchanged"
            elif change > 0:
                improvements[score_name] += 1
                change_type = "improved"
            else:
                regressions[score_name] += 1
                change_type = "regressed"
            
            item_level_changes.append({
                "item_id": item_id,
                "score_name": score_name,
                "run1_value": score1,
                "run2_value": score2,
                "change": change,
                "change_type": change_type,
            })
    
    return RunComparison(
        run1_id=run1.run_id,
        run2_id=run2.run_id,
        run1_scores=run1_scores,
        run2_scores=run2_scores,
        improvements=improvements,
        regressions=regressions,
        unchanged=unchanged,
        item_level_changes=item_level_changes,
    )


def get_regressions(comparison: RunComparison, min_regressions: int = 1) -> dict[str, int]:
    """
    Get score names with regressions above threshold.
    
    Useful for CI/CD to fail builds on regressions.
    
    Args:
        comparison: RunComparison result
        min_regressions: Minimum number of regressions to report
    
    Returns:
        Dictionary of score_name -> regression count
    """
    return {
        name: count
        for name, count in comparison.regressions.items()
        if count >= min_regressions
    }
