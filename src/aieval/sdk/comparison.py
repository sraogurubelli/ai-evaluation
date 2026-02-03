"""Experiment comparison and diffing (Braintrust-style).

Provides side-by-side comparison of experiment runs with regression detection.
"""

from typing import Any
from dataclasses import dataclass, field
from aieval.core.types import ExperimentRun, Score, DatasetItem


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


def compare_multiple_runs(
    runs: list[ExperimentRun],
    model_names: list[str | None] | None = None,
) -> dict[str, Any]:
    """
    Compare multiple experiment runs (one per model) and generate scoreboard.
    
    Similar to ml-infra/evals scoreboard, this provides:
    - Mean scores per model per scorer
    - Model comparison across all scorers
    - Summary statistics
    
    Args:
        runs: List of experiment runs (one per model)
        model_names: Optional list of model names (if None, uses run.run_id)
    
    Returns:
        Dictionary with comparison metrics and scoreboard data
    
    Example:
        runs = [run_claude, run_gpt4]
        comparison = compare_multiple_runs(runs, ["claude-3-7-sonnet", "gpt-4o"])
        print(comparison["scoreboard"])
    """
    if not runs:
        return {
            "scoreboard": {},
            "summary": {},
            "model_scores": {},
        }
    
    # Use provided model names or generate from run IDs
    if model_names is None:
        model_names = [f"model_{i}" for i in range(len(runs))]
    elif len(model_names) != len(runs):
        # Pad or truncate to match runs length
        if len(model_names) < len(runs):
            model_names.extend([f"model_{i}" for i in range(len(model_names), len(runs))])
        else:
            model_names = model_names[:len(runs)]
    
    # Group scores by scorer name and model
    # Structure: scorer_name -> model_name -> list of scores
    scorer_scores: dict[str, dict[str, list[float]]] = {}
    
    for run, model_name in zip(runs, model_names):
        model_display = model_name or "default"
        
        # Group scores by scorer name
        for score in run.scores:
            scorer_name = score.name
            if scorer_name not in scorer_scores:
                scorer_scores[scorer_name] = {}
            if model_display not in scorer_scores[scorer_name]:
                scorer_scores[scorer_name][model_display] = []
            
            # Convert score value to float
            val = score.value
            if isinstance(val, bool):
                val = float(val)
            elif val is None:
                continue
            else:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    continue
            
            scorer_scores[scorer_name][model_display].append(val)
    
    # Calculate statistics per scorer per model
    scoreboard: dict[str, dict[str, dict[str, float]]] = {}
    model_scores: dict[str, dict[str, float]] = {}
    
    for scorer_name, model_data in scorer_scores.items():
        scoreboard[scorer_name] = {}
        
        for model_name, scores in model_data.items():
            if not scores:
                continue
            
            # Calculate mean, handling NaN values
            valid_scores = [s for s in scores if not (isinstance(s, float) and (s != s or s == float('inf') or s == float('-inf')))]
            
            if not valid_scores:
                mean_score = float('nan')
            else:
                mean_score = sum(valid_scores) / len(valid_scores)
            
            scoreboard[scorer_name][model_name] = {
                "mean": round(mean_score, 4),
                "count": len(valid_scores),
                "total": len(scores),
            }
            
            # Track per-model scores
            if model_name not in model_scores:
                model_scores[model_name] = {}
            model_scores[model_name][scorer_name] = mean_score
    
    # Generate summary
    summary = {
        "total_models": len(model_names),
        "total_scorers": len(scorer_scores),
        "scorers": list(scorer_scores.keys()),
        "models": [m or "default" for m in model_names],
    }
    
    return {
        "scoreboard": scoreboard,
        "summary": summary,
        "model_scores": model_scores,
    }
