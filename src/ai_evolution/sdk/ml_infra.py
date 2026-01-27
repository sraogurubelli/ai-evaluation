"""ML Infra SDK helpers for easy migration from ml-infra/evals.

This module provides convenience functions and helpers specifically designed
for ML Infra's evaluation workflow, making migration from ml-infra/evals easier.
"""

import logging
from pathlib import Path
from typing import Any

from ai_evolution import (
    Experiment,
    HTTPAdapter,
    DeepDiffScorer,
    load_index_csv_dataset,
    CSVSink,
    StdoutSink,
)
from ai_evolution.core.types import DatasetItem, ExperimentRun

logger = logging.getLogger(__name__)


def create_ml_infra_experiment(
    index_file: str | Path,
    base_dir: str | Path = "benchmarks/datasets",
    entity_type: str | None = None,
    operation_type: str | None = None,
    offline: bool = False,
    actual_suffix: str = "actual",
    deep_diff_versions: list[str] | None = None,
) -> Experiment:
    """
    Create an experiment configured for ML Infra workflow.
    
    This is a convenience function that matches ml-infra/evals patterns.
    
    Args:
        index_file: Path to index.csv file
        base_dir: Base directory for dataset files
        entity_type: Filter by entity type (optional)
        operation_type: Filter by operation type (optional)
        offline: Use offline mode (load pre-generated outputs)
        actual_suffix: Suffix for actual files (default: "actual")
        deep_diff_versions: List of DeepDiff versions to use (default: ["v3", "v2", "v1"])
    
    Returns:
        Configured Experiment instance
    
    Example:
        experiment = create_ml_infra_experiment(
            index_file="benchmarks/datasets/index.csv",
            base_dir="benchmarks/datasets",
            entity_type="pipeline",
            operation_type="create",
        )
    """
    # Load dataset
    dataset = load_index_csv_dataset(
        index_file=index_file,
        base_dir=base_dir,
        entity_type=entity_type,
        operation_type=operation_type,
        offline=offline,
        actual_suffix=actual_suffix,
    )
    
    # Create scorers (default to v3, v2, v1 like ml-infra/evals)
    if deep_diff_versions is None:
        deep_diff_versions = ["v3", "v2", "v1"]
    
    scorers = []
    for version in deep_diff_versions:
        scorers.append(
            DeepDiffScorer(
                name=f"deep_diff_{version}",
                eval_id=f"deep_diff_{version}.v1",
                version=version,
            )
        )
    
    # Create experiment
    experiment_name = f"ml_infra_{entity_type or 'all'}_{operation_type or 'all'}"
    if offline:
        experiment_name += "_offline"
    
    return Experiment(
        name=experiment_name,
        dataset=dataset,
        scorers=scorers,
    )


async def run_ml_infra_eval(
    index_file: str | Path,
    base_dir: str | Path = "benchmarks/datasets",
    entity_type: str | None = None,
    operation_type: str | None = None,
    model: str | None = None,
    base_url: str = "http://localhost:8000",
    auth_token: str = "",
    account_id: str = "default",
    org_id: str = "default",
    project_id: str = "default",
    offline: bool = False,
    actual_suffix: str = "actual",
    output_csv: str | Path | None = None,
    concurrency_limit: int = 5,
    deep_diff_versions: list[str] | None = None,
) -> ExperimentRun:
    """
    Run ML Infra evaluation (convenience function matching ml-infra/evals workflow).
    
    This function provides a simple interface similar to ml-infra/evals benchmark_evals.py.
    
    Args:
        index_file: Path to index.csv file
        base_dir: Base directory for dataset files
        entity_type: Filter by entity type
        operation_type: Filter by operation type
        model: Model name to use
        base_url: ML Infra server base URL
        auth_token: Authentication token
        account_id: Account ID
        org_id: Organization ID
        project_id: Project ID
        offline: Use offline mode
        actual_suffix: Suffix for actual files
        output_csv: Path to output CSV file (optional)
        concurrency_limit: Maximum concurrent API calls
        deep_diff_versions: List of DeepDiff versions to use
    
    Returns:
        ExperimentRun result
    
    Example:
        result = await run_ml_infra_eval(
            index_file="benchmarks/datasets/index.csv",
            entity_type="pipeline",
            operation_type="create",
            model="claude-3-7-sonnet-20250219",
            output_csv="results/pipeline_create.csv",
        )
    """
    # Create experiment
    experiment = create_ml_infra_experiment(
        index_file=index_file,
        base_dir=base_dir,
        entity_type=entity_type,
        operation_type=operation_type,
        offline=offline,
        actual_suffix=actual_suffix,
        deep_diff_versions=deep_diff_versions,
    )
    
    # Create adapter (only if not offline)
    adapter = None
    if not offline:
        adapter = HTTPAdapter(
            base_url=base_url,
            auth_token=auth_token,
            account_id=account_id,
            org_id=org_id,
            project_id=project_id,
        )
    
    # Create sinks
    sinks = [StdoutSink()]
    if output_csv:
        sinks.append(CSVSink(output_csv))
    
    # Run experiment
    if offline:
        # For offline mode, we need to score existing outputs
        # This requires a different approach - scores are generated from existing outputs
        from ai_evolution.core.experiment import Experiment
        # Note: Offline mode requires outputs to be pre-populated in dataset
        # The experiment will score them directly
        pass
    
    result = await experiment.run(
        adapter=adapter,
        model=model,
        concurrency_limit=concurrency_limit,
    )
    
    # Emit to sinks
    for sink in sinks:
        sink.emit_run(result)
        sink.flush()
    
    return result


def compare_csv_results(
    csv1_path: str | Path,
    csv2_path: str | Path,
    tolerance: float = 0.01,
) -> dict[str, Any]:
    """
    Compare two CSV result files (useful for validating migration).
    
    Compares scores between two CSV files and reports differences.
    
    Args:
        csv1_path: Path to first CSV (e.g., ml-infra/evals output)
        csv2_path: Path to second CSV (e.g., ai-evolution output)
        tolerance: Tolerance for score differences
    
    Returns:
        Dictionary with comparison results
    
    Example:
        comparison = compare_csv_results(
            csv1_path="ml-infra/evals/results.csv",
            csv2_path="ai-evolution/results.csv",
        )
        print(f"Matches: {comparison['matches']}, Differences: {comparison['differences']}")
    """
    import pandas as pd
    
    csv1_path = Path(csv1_path)
    csv2_path = Path(csv2_path)
    
    if not csv1_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv1_path}")
    if not csv2_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv2_path}")
    
    # Load CSVs
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)
    
    # Compare structure
    comparison = {
        "csv1_rows": len(df1),
        "csv2_rows": len(df2),
        "csv1_columns": list(df1.columns),
        "csv2_columns": list(df2.columns),
        "matches": 0,
        "differences": 0,
        "missing_in_csv2": [],
        "missing_in_csv1": [],
        "score_differences": [],
    }
    
    # Find common test IDs (assuming test_id column exists)
    if "test_id" in df1.columns and "test_id" in df2.columns:
        test_ids1 = set(df1["test_id"])
        test_ids2 = set(df2["test_id"])
        common_test_ids = test_ids1 & test_ids2
        comparison["common_test_ids"] = len(common_test_ids)
        
        # Track missing test IDs
        comparison["missing_in_csv2"] = sorted(list(test_ids1 - test_ids2))
        comparison["missing_in_csv1"] = sorted(list(test_ids2 - test_ids1))
        
        # Compare scores for common test IDs
        for test_id in common_test_ids:
            row1 = df1[df1["test_id"] == test_id].iloc[0] if len(df1[df1["test_id"] == test_id]) > 0 else None
            row2 = df2[df2["test_id"] == test_id].iloc[0] if len(df2[df2["test_id"] == test_id]) > 0 else None
            
            if row1 is None or row2 is None:
                comparison["differences"] += 1
                continue
            
            # Compare score columns
            score_columns = [col for col in df1.columns if "deep_diff" in col.lower() or "score" in col.lower()]
            for col in score_columns:
                if col in row1 and col in row2:
                    val1 = row1[col]
                    val2 = row2[col]
                    
                    # Handle NaN
                    if pd.isna(val1) and pd.isna(val2):
                        comparison["matches"] += 1
                        continue
                    if pd.isna(val1) or pd.isna(val2):
                        comparison["differences"] += 1
                        comparison["score_differences"].append({
                            "test_id": test_id,
                            "column": col,
                            "csv1": val1,
                            "csv2": val2,
                        })
                        continue
                    
                    # Compare numeric values
                    diff = abs(float(val1) - float(val2))
                    if diff <= tolerance:
                        comparison["matches"] += 1
                    else:
                        comparison["differences"] += 1
                        comparison["score_differences"].append({
                            "test_id": test_id,
                            "column": col,
                            "csv1": val1,
                            "csv2": val2,
                            "difference": diff,
                        })
    
    return comparison


def create_ml_infra_sinks(
    output_dir: str | Path = "results",
    experiment_name: str = "experiment",
    include_stdout: bool = True,
) -> list:
    """
    Create sinks configured for ML Infra workflow.
    
    Args:
        output_dir: Directory for output files
        experiment_name: Name of the experiment
        include_stdout: Whether to include stdout sink
    
    Returns:
        List of sink instances
    """
    from datetime import datetime
    import time
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sinks = []
    
    if include_stdout:
        sinks.append(StdoutSink())
    
    # CSV sink with timestamp
    timestamp = int(time.time())
    csv_path = output_dir / f"{experiment_name}_{timestamp}.csv"
    sinks.append(CSVSink(csv_path))
    
    return sinks
