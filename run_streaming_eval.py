"""Run streaming evaluation using SSEStreamingAdapter.

This script evaluates datasets from ml-infra/evals/benchmarks using SSE streaming
to collect YAML quality scores, performance metrics, and tool call information.

Usage:
    python run_streaming_eval.py
    python run_streaming_eval.py --entity-type pipeline --operation-type create
    python run_streaming_eval.py --test-id pipeline_create_001
"""

import asyncio
import argparse
import os
import logging
import json
import uuid
from pathlib import Path
from typing import Any
import sys

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streaming_eval.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

# Add ai-evolution src to path
ai_evolution_path = Path(__file__).parent / "src"
sys.path.insert(0, str(ai_evolution_path))

from ai_evolution.adapters.sse_streaming import SSEStreamingAdapter
from ai_evolution.scorers.enriched import EnrichedOutputScorer
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.scorers.metrics import LatencyScorer, TokenUsageScorer
from ai_evolution.datasets.index_csv import load_index_csv_dataset
from ai_evolution.core.experiment import Experiment
from ai_evolution.core.types import ExperimentRun, Score
from ai_evolution.sinks.csv import CSVSink
from ai_evolution.sinks.stdout import StdoutSink


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run streaming evaluation with SSEStreamingAdapter"
    )
    parser.add_argument(
        "--entity-type",
        default="pipeline",
        help="Entity type filter (default: pipeline)"
    )
    parser.add_argument(
        "--operation-type",
        default="create",
        help="Operation type filter (default: create)"
    )
    parser.add_argument(
        "--test-id",
        help="Specific test ID to run (optional)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Concurrent requests (default: 5)"
    )
    parser.add_argument(
        "--output",
        default="results/streaming_eval.csv",
        help="Output CSV file (default: results/streaming_eval.csv)"
    )
    parser.add_argument(
        "--model",
        default="claude-3-7-sonnet-20250219",
        help="Model to use (default: claude-3-7-sonnet-20250219)"
    )
    parser.add_argument(
        "--max-latency",
        type=int,
        default=30000,
        help="Max latency threshold in ms (default: 30000)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=10000,
        help="Max token budget (default: 10000)"
    )
    return parser.parse_args()


def build_httpAdapter_compatible_payload(input_data: dict[str, Any], model: str | None) -> dict[str, Any]:
    """Build payload matching HTTPAdapter format.
    
    This ensures the SSEStreamingAdapter sends the exact same payload structure
    as HTTPAdapter, maintaining API compatibility while gaining streaming capabilities.
    """
    # Determine provider from model
    provider = "anthropic" if model and "claude" in model.lower() else "openai"
    
    # Build action string
    entity_type = input_data.get("entity_type", "pipeline").upper()
    operation_type = input_data.get("operation_type", "create").upper()
    action = f"{operation_type}_{entity_type}"
    
    payload = {
        "prompt": input_data.get("prompt", ""),
        "conversation_id": str(uuid.uuid4()),
        "interaction_id": str(uuid.uuid4()),
        "provider": provider,
        "model_name": model,
        "action": action,
        "conversation_raw": [],
        "stream": True,
        "capabilities": [
            {"type": "display_yaml", "version": "0"},
            {"type": "display_error", "version": "0"},
        ],
        "context": [],
        "harness_context": {
            "account_id": os.getenv("ACCOUNT_ID", "kmpySmUISimoRrJL6NL73w"),
            "org_id": os.getenv("ORG_ID", "default"),
            "project_id": os.getenv("PROJECT_ID", "test_project"),
        },
    }
    
    # Add old_yaml for update operations
    if operation_type.lower() == "update" and "old_yaml" in input_data:
        payload["conversation_raw"] = [
            {"role": "assistant", "content": input_data["old_yaml"]}
        ]
    
    return payload


def calculate_avg_score(scores: list[Score], scorer_name: str) -> float:
    """Calculate average score for a specific scorer."""
    relevant_scores = [s.value for s in scores if s.name == scorer_name]
    return sum(relevant_scores) / len(relevant_scores) if relevant_scores else 0.0


def calculate_avg_metric(scores: list[Score], metric_name: str) -> float:
    """Calculate average metric value from score metadata."""
    values = []
    for score in scores:
        if metric_name in score.metadata:
            values.append(score.metadata[metric_name])
    return sum(values) / len(values) if values else 0.0


def print_summary_report(result: ExperimentRun, args: argparse.Namespace):
    """Print comprehensive summary report."""
    print("\n" + "=" * 80)
    print("STREAMING EVALUATION SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 Configuration:")
    print(f"   Entity Type: {args.entity_type}")
    print(f"   Operation Type: {args.operation_type}")
    print(f"   Model: {args.model}")
    print(f"   Concurrency: {args.concurrency}")
    
    print(f"\n📈 Results:")
    print(f"   Run ID: {result.run_id}")
    print(f"   Total Tests: {len(result.scores) // 3}")  # 3 scorers per test
    print(f"   Total Scores: {len(result.scores)}")
    
    # Calculate averages
    avg_yaml = calculate_avg_score(result.scores, "deep_diff_v3")
    avg_latency = calculate_avg_metric(result.scores, "latency_ms")
    avg_tokens = calculate_avg_metric(result.scores, "total_tokens")
    avg_prompt_tokens = calculate_avg_metric(result.scores, "prompt_tokens")
    avg_completion_tokens = calculate_avg_metric(result.scores, "completion_tokens")
    
    print(f"\n🎯 Quality Metrics:")
    print(f"   Average YAML Score: {avg_yaml:.3f}")
    
    print(f"\n⚡ Performance Metrics:")
    print(f"   Average Latency: {avg_latency:.0f}ms")
    print(f"   Average Total Tokens: {avg_tokens:.0f}")
    print(f"   Average Prompt Tokens: {avg_prompt_tokens:.0f}")
    print(f"   Average Completion Tokens: {avg_completion_tokens:.0f}")
    
    # Count tests with tools
    tool_counts = []
    for score in result.scores:
        if "tool_count" in score.metadata:
            tool_counts.append(score.metadata["tool_count"])
    
    if tool_counts:
        avg_tools = sum(tool_counts) / len(tool_counts)
        tests_with_tools = sum(1 for c in tool_counts if c > 0)
        print(f"\n🔧 Tool Usage:")
        print(f"   Tests Using Tools: {tests_with_tools}/{len(tool_counts)}")
        print(f"   Average Tools per Test: {avg_tools:.1f}")
    
    print(f"\n💾 Output:")
    print(f"   CSV File: {args.output}")
    print(f"   YAML Files: ../ml-infra/evals/benchmarks/datasets/*_actual.yaml")
    
    print("\n" + "=" * 80)


async def main():
    """Run streaming evaluation."""
    args = parse_args()
    
    print("=" * 80)
    print("STREAMING EVALUATION: SSE Adapter with Performance Metrics")
    print("=" * 80)
    
    # Load dataset
    print(f"\n📂 Loading dataset...")
    print(f"   Entity Type: {args.entity_type}")
    print(f"   Operation Type: {args.operation_type}")
    if args.test_id:
        print(f"   Test ID: {args.test_id}")
    
    dataset = load_index_csv_dataset(
        index_file="../ml-infra/evals/benchmarks/datasets/index.csv",
        base_dir="../ml-infra/evals/benchmarks/datasets",
        entity_type=args.entity_type,
        operation_type=args.operation_type,
        test_id=args.test_id,
    )
    
    print(f"   ✅ Loaded {len(dataset)} test cases")
    
    # Create adapter with HTTPAdapter-compatible payload
    print(f"\n🔌 Creating SSEStreamingAdapter...")
    adapter = SSEStreamingAdapter(
        base_url=os.getenv("CHAT_BASE_URL", "http://localhost:8000"),
        headers={
            "Authorization": f"Bearer {os.getenv('CHAT_PLATFORM_AUTH_TOKEN', 'token')}"
        },
        endpoint="/chat/platform",
        completion_events=["final_yaml_created"],
        tool_call_events=["tool_call", "function_call"],
        usage_event="model_usage",
        payload_builder=build_httpAdapter_compatible_payload,
    )
    print(f"   ✅ Adapter configured")
    
    # Create scorers
    print(f"\n📊 Creating scorers...")
    
    # 1. YAML Quality scorer (wrapped for enriched output)
    yaml_scorer = EnrichedOutputScorer(
        DeepDiffScorer(
            name="deep_diff_v3",
            eval_id="deep_diff_v3.v1",
            version="v3"
        )
    )
    
    # 2. Latency scorer
    latency_scorer = LatencyScorer(
        max_latency_ms=args.max_latency,
        name="latency",
        eval_id="latency.v1"
    )
    
    # 3. Token usage scorer
    token_scorer = TokenUsageScorer(
        max_tokens=args.max_tokens,
        name="token_usage",
        eval_id="token_usage.v1"
    )
    
    scorers = [yaml_scorer, latency_scorer, token_scorer]
    print(f"   ✅ Created {len(scorers)} scorers")
    
    # Create experiment
    print(f"\n🧪 Creating experiment...")
    experiment = Experiment(
        name="streaming_eval", 
        dataset=dataset,
        scorers=scorers,
        experiment_id="streaming_eval",
    )
    print(f"   ✅ Experiment created")
    
    # Run experiment
    print(f"\n🚀 Running evaluation...")
    print(f"   Model: {args.model}")
    print(f"   Concurrency: {args.concurrency}")
    print(f"   This may take a few minutes...\n")
    
    result = await experiment.run(
        adapter=adapter,
        model=args.model,
        concurrency_limit=args.concurrency,
    )
    
    print(f"\n✅ Evaluation completed!")
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    print(f"\n💾 Saving results...")
    sinks = [
        CSVSink(args.output),
    ]
    
    for sink in sinks:
        sink.emit_run(result)
        sink.flush()
    
    print(f"   ✅ Results saved to: {args.output}")
    
    # Save generated YAML files
    print(f"\n📝 Saving generated YAML files...")
    base_dir = Path("../ml-infra/evals/benchmarks/datasets")
    saved_count = 0
    
    for item in experiment.dataset:
        if item.output:
            try:
                # Parse enriched JSON to extract final_yaml
                enriched = json.loads(item.output)
                final_yaml = enriched.get("final_yaml", "")
                
                if final_yaml:
                    # Get expected file path from metadata
                    expected_file = base_dir / item.metadata["expected_file"]
                    
                    # Create actual file: 001_expected.yaml -> 001_actual.yaml
                    actual_file = expected_file.parent / expected_file.name.replace("_expected.", "_actual.")
                    
                    # Save generated output
                    actual_file.write_text(final_yaml, encoding="utf-8")
                    saved_count += 1
                    print(f"   ✅ Saved: {actual_file.relative_to(base_dir)}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to extract YAML for {item.id}: {e}")
    
    print(f"\n✅ Saved {saved_count} generated YAML files")
    
    # Print summary report
    print_summary_report(result, args)


if __name__ == "__main__":
    asyncio.run(main())
