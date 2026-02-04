"""DevOps consumer SDK – helpers for DevOps/Harness evaluation workflow.

Consumer-side implementation using the agent-agnostic aieval SDK.
Generic helpers (score_single_output, run_single_item) are in aieval.sdk.unit_test.
"""

import logging
from pathlib import Path
from typing import Any

from aieval import (
    Experiment,
    HTTPAdapter,
    DeepDiffScorer,
    load_index_csv_dataset,
    CSVSink,
    StdoutSink,
    JUnitSink,
    HTMLReportSink,
)
from aieval.adapters.sse_streaming import SSEStreamingAdapter
from aieval.scorers.enriched import EnrichedOutputScorer
from aieval.scorers.metrics import LatencyScorer, ToolCallScorer, TokenUsageScorer
from aieval.core.types import DatasetItem, ExperimentRun, Score
from aieval.scorers.base import Scorer
from aieval.adapters.base import Adapter
from aieval.sdk.unit_test import score_single_output, run_single_item

logger = logging.getLogger(__name__)


def create_devops_experiment(
    index_file: str | Path,
    base_dir: str | Path = "benchmarks/datasets",
    entity_type: str | None = None,
    operation_type: str | None = None,
    offline: bool = False,
    actual_suffix: str = "actual",
    deep_diff_versions: list[str] | None = None,
    use_enriched_output: bool = False,
    include_metric_scorers: bool = False,
) -> Experiment:
    """
    Create an experiment configured for DevOps (e.g. Harness) workflow.

    Args:
        index_file: Path to index.csv file
        base_dir: Base directory for dataset files
        entity_type: Filter by entity type (optional)
        operation_type: Filter by operation type (optional)
        offline: Use offline mode (load pre-generated outputs)
        actual_suffix: Suffix for actual files (default: "actual")
        deep_diff_versions: List of DeepDiff versions to use (default: ["v3", "v2", "v1"])
        use_enriched_output: If True, wrap scorers with EnrichedOutputScorer for SSE enriched output
        include_metric_scorers: If True, add metric scorers (LatencyScorer, ToolCallScorer, TokenUsageScorer)

    Returns:
        Configured Experiment instance
    """
    dataset = load_index_csv_dataset(
        index_file=index_file,
        base_dir=base_dir,
        entity_type=entity_type,
        operation_type=operation_type,
        offline=offline,
        actual_suffix=actual_suffix,
    )

    if deep_diff_versions is None:
        deep_diff_versions = ["v3", "v2", "v1"]

    scorers = []
    for version in deep_diff_versions:
        base_scorer = DeepDiffScorer(
            name=f"deep_diff_{version}",
            eval_id=f"deep_diff_{version}.v1",
            version=version,
        )
        scorer = EnrichedOutputScorer(base_scorer) if use_enriched_output else base_scorer
        scorers.append(scorer)

    if include_metric_scorers:
        scorers.append(
            LatencyScorer(
                max_latency_ms=30000,
                name="latency",
                eval_id="latency.v1",
            )
        )
        scorers.append(
            ToolCallScorer(
                name="tool_calls",
                eval_id="tool_calls.v1",
                require_tools=False,
            )
        )
        scorers.append(
            TokenUsageScorer(
                max_tokens=10000,
                name="token_usage",
                eval_id="token_usage.v1",
            )
        )

    experiment_name = f"devops_{entity_type or 'all'}_{operation_type or 'all'}"
    if offline:
        experiment_name += "_offline"

    return Experiment(
        name=experiment_name,
        dataset=dataset,
        scorers=scorers,
    )


async def run_devops_eval(
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
    use_sse_streaming: bool = False,
    include_metric_scorers: bool = False,
    agent_id: str = "devops-pipeline-agent",
    agent_name: str = "unknown",
    agent_version: str = "unknown",
    output_junit: str | Path | None = None,
    output_html: str | Path | None = None,
) -> ExperimentRun:
    """
    Run DevOps evaluation (convenience function matching Harness/DevOps evals workflow).
    agent_id is the unique identifier for grouping runs in the platform (e.g. GET /agents/{agent_id}/runs).
    """
    experiment = create_devops_experiment(
        index_file=index_file,
        base_dir=base_dir,
        entity_type=entity_type,
        operation_type=operation_type,
        offline=offline,
        actual_suffix=actual_suffix,
        deep_diff_versions=deep_diff_versions,
        use_enriched_output=use_sse_streaming,
        include_metric_scorers=include_metric_scorers,
    )

    adapter = None
    if not offline:
        if use_sse_streaming:
            logger.info("Creating DevOps adapter (SSE streaming)")
            adapter = SSEStreamingAdapter(
                base_url=base_url,
                headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
                context_data={
                    "account_id": account_id,
                    "org_id": org_id,
                    "project_id": project_id,
                },
                endpoint="/chat/stream",
                completion_events=[
                    "complete",
                    "dashboard_complete",
                    "kg_complete",
                ],
                tool_call_events=[
                    "tool_call",
                    "function_call",
                ],
                include_uuids=True,
            )
        else:
            logger.info("Creating HTTP adapter")
            adapter = HTTPAdapter(
                base_url=base_url,
                auth_token=auth_token,
                context_field_name="harness_context",
                context_data={
                    "account_id": account_id,
                    "org_id": org_id,
                    "project_id": project_id,
                },
                endpoint_mapping={
                    "dashboard": "/chat/dashboard",
                    "knowledge_graph": "/chat/knowledge-graph",
                },
                default_endpoint="/chat/platform",
                yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
                sse_completion_events=["dashboard_complete", "kg_complete"],
            )

    sinks: list[Any] = [StdoutSink()]
    if output_csv:
        sinks.append(CSVSink(output_csv))
    if output_junit:
        sinks.append(JUnitSink(Path(output_junit)))
    if output_html:
        sinks.append(HTMLReportSink(Path(output_html)))

    result = await experiment.run(
        adapter=adapter,
        model=model,
        concurrency_limit=concurrency_limit,
        agent_id=agent_id,
        agent_name=agent_name,
        agent_version=agent_version,
    )

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
    """
    import pandas as pd

    csv1_path = Path(csv1_path)
    csv2_path = Path(csv2_path)

    if not csv1_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv1_path}")
    if not csv2_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv2_path}")

    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

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

    if "test_id" in df1.columns and "test_id" in df2.columns:
        test_ids1 = set(df1["test_id"])
        test_ids2 = set(df2["test_id"])
        common_test_ids = test_ids1 & test_ids2
        comparison["common_test_ids"] = len(common_test_ids)
        comparison["missing_in_csv2"] = sorted(list(test_ids1 - test_ids2))
        comparison["missing_in_csv1"] = sorted(list(test_ids2 - test_ids1))

        for test_id in common_test_ids:
            row1 = df1[df1["test_id"] == test_id].iloc[0] if len(df1[df1["test_id"] == test_id]) > 0 else None
            row2 = df2[df2["test_id"] == test_id].iloc[0] if len(df2[df2["test_id"] == test_id]) > 0 else None

            if row1 is None or row2 is None:
                comparison["differences"] += 1
                continue

            score_columns = [col for col in df1.columns if "deep_diff" in col.lower() or "score" in col.lower()]
            for col in score_columns:
                if col in row1 and col in row2:
                    val1 = row1[col]
                    val2 = row2[col]

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


def create_devops_sinks(
    output_dir: str | Path = "results",
    experiment_name: str = "experiment",
    include_stdout: bool = True,
) -> list:
    """Create sinks configured for DevOps workflow."""
    import time

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sinks = []
    if include_stdout:
        sinks.append(StdoutSink())

    timestamp = int(time.time())
    csv_path = output_dir / f"{experiment_name}_{timestamp}.csv"
    sinks.append(CSVSink(csv_path))

    return sinks


def load_single_test_case(
    index_file: str | Path,
    test_id: str,
    base_dir: str | Path = "benchmarks/datasets",
    offline: bool = False,
    actual_suffix: str = "actual",
) -> DatasetItem:
    """
    Load a single test case by test_id (convenience function for unit testing).
    """
    dataset = load_index_csv_dataset(
        index_file=index_file,
        base_dir=base_dir,
        test_id=test_id,
        offline=offline,
        actual_suffix=actual_suffix,
    )

    if len(dataset) == 0:
        raise ValueError(f"Test case '{test_id}' not found in index file")
    if len(dataset) > 1:
        raise ValueError(f"Multiple test cases found for '{test_id}' (expected 1)")

    return dataset[0]


async def run_single_test(
    test_id: str,
    index_file: str | Path,
    adapter: Adapter,
    scorer: Scorer,
    model: str | None = None,
    base_dir: str | Path = "benchmarks/datasets",
    concurrency_limit: int = 1,
) -> ExperimentRun:
    """
    Run a single test case end-to-end (convenience function for unit testing).
    Uses framework run_single_item under the hood.
    """
    test_case = load_single_test_case(
        index_file=index_file,
        test_id=test_id,
        base_dir=base_dir,
    )
    return await run_single_item(
        dataset_item=test_case,
        adapter=adapter,
        scorer=scorer,
        model=model,
        concurrency_limit=concurrency_limit,
    )


async def verify_test_compatibility(
    test_id: str,
    index_file: str | Path = "benchmarks/datasets/index.csv",
    legacy_results_csv: str | Path | None = None,
    aieval_results_csv: str | Path | None = None,
    tolerance: float = 0.01,
    base_dir: str | Path = "benchmarks/datasets",
) -> bool:
    """
    Verify that a test case produces compatible results between legacy evals and ai-evolution.
    """
    import glob
    import os

    if legacy_results_csv is None:
        possible_paths = [
            "ml-infra/evals/results.csv",
            "results/devops.csv",
            "results/results.csv",
        ]
        for path in possible_paths:
            if Path(path).exists():
                legacy_results_csv = path
                break

    if aieval_results_csv is None:
        result_files = glob.glob("results/*.csv") + glob.glob("ai-evolution/results/*.csv")
        if result_files:
            aieval_results_csv = max(result_files, key=os.path.getmtime)

    if legacy_results_csv is None or aieval_results_csv is None:
        logger.warning(
            "Could not find result CSV files. "
            "Please provide legacy_results_csv and aieval_results_csv paths."
        )
        return False

    comparison = compare_csv_results(
        csv1_path=legacy_results_csv,
        csv2_path=aieval_results_csv,
        tolerance=tolerance,
    )

    if comparison["differences"] == 0:
        return True

    score_diffs = [
        diff for diff in comparison["score_differences"]
        if diff.get("test_id") == test_id
    ]

    if len(score_diffs) == 0:
        return True

    for diff in score_diffs:
        if diff.get("difference", float("inf")) > tolerance:
            logger.warning(f"Test {test_id} has score difference > tolerance: {diff}")
            return False

    return True
