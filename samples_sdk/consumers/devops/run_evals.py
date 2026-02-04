#!/usr/bin/env python3
"""Run DevOps evals from the command line.

Run from ai-evaluation repo root:

    python samples_sdk/consumers/devops/run_evals.py --agent-id devops-pipeline-agent --entity-type pipeline

With streaming and metrics:

    python samples_sdk/consumers/devops/run_evals.py \\
      --agent-id devops-pipeline-agent --entity-type pipeline \\
      --agent-name DevopsAgent --agent-version 0.1 \\
      --streaming --include-metrics --concurrency 1

--agent-id is the unique identifier for this agent; runs are grouped by agent_id in the platform (e.g. GET /agents/{agent_id}/runs).
--agent-name and --agent-version are optional display metadata.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure repo root (or ai-evaluation) is on path so samples_sdk is importable
# File is at: samples_sdk/consumers/devops/run_evals.py
# So we need to go up 3 levels to reach repo root
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from samples_sdk.consumers.devops import (
    create_devops_experiment,
    run_devops_eval,
    create_devops_sinks,
)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run DevOps evals. Use --agent-id for unique agent grouping (e.g. in platform UI)."
    )
    parser.add_argument(
        "--agent-id",
        default="devops-pipeline-agent",
        help="Unique identifier for the agent (default: devops-pipeline-agent). Used for grouping runs in platform.",
    )
    parser.add_argument(
        "--entity-type",
        default="pipeline",
        help="Entity type filter (default: pipeline).",
    )
    parser.add_argument(
        "--operation-type",
        default="create",
        help="Operation type filter (default: create).",
    )
    parser.add_argument(
        "--agent-name",
        default="DevopsAgent",
        help="Display name for the agent (default: DevopsAgent).",
    )
    parser.add_argument(
        "--agent-version",
        default="0.1",
        help="Display version for the agent (default: 0.1).",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use SSE streaming adapter.",
    )
    parser.add_argument(
        "--include-metrics",
        action="store_true",
        help="Include metric scorers (latency, tool_calls, token_usage).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Concurrency limit (default: 1).",
    )
    parser.add_argument(
        "--index-file",
        default="benchmarks/datasets/index.csv",
        help="Path to index.csv (default: benchmarks/datasets/index.csv).",
    )
    parser.add_argument(
        "--base-dir",
        default="benchmarks/datasets",
        help="Base directory for dataset files (default: benchmarks/datasets).",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the agent/chat service (default: http://localhost:8000).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Offline mode (load pre-generated outputs, skip adapter).",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Optional path for output CSV.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (e.g. claude-3-7-sonnet).",
    )
    parser.add_argument(
        "--junit",
        default=None,
        metavar="PATH",
        help="Write JUnit XML to PATH (e.g. results/junit.xml) for CI.",
    )
    parser.add_argument(
        "--html",
        default=None,
        metavar="PATH",
        help="Write HTML report to PATH (e.g. results/report.html).",
    )
    return parser.parse_args()


async def main():
    args = _parse_args()
    index_file = Path(args.index_file)
    if not index_file.exists():
        print(f"Index file not found: {index_file}. Create it and add test cases, then re-run.")
        return 1

    print("Creating DevOps experiment...")
    print(f"  agent_id: {args.agent_id} (unique)")
    print(f"  entity_type: {args.entity_type}, operation_type: {args.operation_type}")
    print(f"  streaming: {args.streaming}, include_metrics: {args.include_metrics}, concurrency: {args.concurrency}")

    if args.offline:
        print("\nOffline mode: skipping run (no adapter). Set --offline=false and ensure server is up to run eval.")
        experiment = create_devops_experiment(
            index_file=str(index_file),
            base_dir=args.base_dir,
            entity_type=args.entity_type,
            operation_type=args.operation_type,
            offline=True,
            use_enriched_output=args.streaming,
            include_metric_scorers=args.include_metrics,
        )
        print(f"  Dataset size: {len(experiment.dataset)}")
        print(f"  Scorers: {[s.name for s in experiment.scorers]}")
        return 0

    print("\nRunning eval...")
    result = await run_devops_eval(
        index_file=str(index_file),
        base_dir=args.base_dir,
        entity_type=args.entity_type,
        operation_type=args.operation_type,
        model=args.model,
        base_url=args.base_url,
        offline=False,
        output_csv=args.output_csv,
        concurrency_limit=args.concurrency,
        use_sse_streaming=args.streaming,
        include_metric_scorers=args.include_metrics,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_version=args.agent_version,
        output_junit=args.junit,
        output_html=args.html,
    )
    print(f"  Run id: {result.run_id}")
    print(f"  Metadata agent_id: {result.metadata.get('agent_id')}")
    print(f"  Scores: {[(s.name, s.value) for s in result.scores]}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
