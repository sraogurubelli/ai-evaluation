"""Example: SSE Streaming Adapter with Enriched Output and Metric Scorers.

This example demonstrates:
1. Using SSEStreamingAdapter to capture streaming events, tools, and metrics
2. Wrapping existing scorers with EnrichedOutputScorer
3. Using new metric-specific scorers (Latency, ToolCall, TokenUsage)
4. Combining YAML quality scores with performance metrics
5. Different configuration approaches for SSEStreamingAdapter

Run this example:
    python examples/sse_streaming_example.py
"""

import asyncio
import os
import uuid
from ai_evolution.adapters.sse_streaming import SSEStreamingAdapter
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.scorers.enriched import EnrichedOutputScorer
from ai_evolution.scorers.metrics import (
    LatencyScorer,
    ToolCallScorer,
    TokenUsageScorer,
)
from ai_evolution.core.types import DatasetItem
from ai_evolution.sdk.runner import run_evaluation


# ============================================================
# Configuration Examples
# ============================================================
# Below are different ways to configure SSEStreamingAdapter
# for various use cases and API formats
# ============================================================

def example_basic_configuration():
    """Example 1: Basic configuration with custom headers."""
    return SSEStreamingAdapter(
        base_url="http://localhost:8000",
        headers={
            "Authorization": f"Bearer {os.getenv('API_TOKEN', 'your-token')}",
            "X-API-Key": os.getenv("API_KEY", "your-key"),
            "X-Tenant-ID": "tenant-123",
        }
    )


def example_httpAdapter_compatible():
    """Example 2: HTTPAdapter-compatible configuration with UUIDs."""
    return SSEStreamingAdapter(
        base_url="http://localhost:8000",
        headers={"Authorization": "Bearer token"},
        include_uuids=True,  # Adds conversation_id, interaction_id
        context_data={
            "account_id": "acc-123",
            "org_id": "org-456",
        }
    )


def example_custom_payload_builder():
    """Example 3: Custom payload builder for complete control."""
    def build_custom_payload(input_data, model):
        return {
            "request_id": str(uuid.uuid4()),
            "prompt": input_data.get("prompt"),
            "model": model,
            "stream": True,
            "options": {"temperature": 0.7}
        }
    
    return SSEStreamingAdapter(
        base_url="http://localhost:8000",
        payload_builder=build_custom_payload
    )


def example_payload_template():
    """Example 4: Payload template with dynamic field mapping."""
    return SSEStreamingAdapter(
        base_url="http://localhost:8000",
        payload_template={
            "id": "__uuid__",                    # Generates UUID
            "query": "__input__.prompt",         # From input_data
            "model_name": "__model__",           # From model param
            "timestamp": "__timestamp__",        # Current time (ms)
            "entity_type": "__input__.entity_type",
            "config": {"stream": True}           # Static value
        }
    )


def example_openai_style_payload():
    """Example 5: OpenAI-style messages format using template."""
    return SSEStreamingAdapter(
        base_url="https://api.example.com",
        headers={"Authorization": "ApiKey your-key"},
        payload_template={
            "messages": [
                {"role": "user", "content": "__input__.prompt"}
            ],
            "model": "__model__",
            "stream": True
        }
    )


async def main():
    """Run SSE streaming evaluation example."""
    
    # ============================================================
    # 1. Create SSEStreamingAdapter
    # ============================================================
    # The SSE adapter captures all streaming events and returns
    # enriched output with metrics, tools, and events
    
    # Choose one of the configuration examples above, or create custom:
    adapter = SSEStreamingAdapter(
        base_url="http://localhost:8000",
        headers={"Authorization": f"Bearer {os.getenv('API_TOKEN', 'your-token')}"},
        context_data={
            "account_id": "acc-123",
            "org_id": "org-456",
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
    )
    
    # Or use one of the example configurations:
    # adapter = example_httpAdapter_compatible()
    # adapter = example_payload_template()
    # adapter = example_custom_payload_builder()
    
    # ============================================================
    # 2. Create Scorers
    # ============================================================
    
    # Wrap existing scorers to work with enriched output
    # The wrapper extracts final_yaml and enriches metadata
    yaml_quality_scorer = EnrichedOutputScorer(
        DeepDiffScorer(
            name="yaml_structure",
            eval_id="structure.v3",
            version="v3"
        )
    )
    
    # Create metric-specific scorers
    # These analyze performance metrics from enriched output
    latency_scorer = LatencyScorer(
        max_latency_ms=30000,  # 30 seconds threshold
        name="latency",
        eval_id="latency.v1",
    )
    
    tool_scorer = ToolCallScorer(
        name="tool_calls",
        eval_id="tool_calls.v1",
        require_tools=False,  # Set to True to require tools
    )
    
    token_scorer = TokenUsageScorer(
        max_tokens=5000,  # Token budget
        name="token_usage",
        eval_id="token_usage.v1",
    )
    
    # ============================================================
    # 3. Create Dataset
    # ============================================================
    
    dataset = [
        DatasetItem(
            id="test_1",
            input={
                "prompt": "Create a CI/CD pipeline with build and deploy stages",
                "entity_type": "pipeline",
                "operation_type": "create",
            },
            expected={
                "yaml": """
pipeline:
  name: ci-cd-pipeline
  stages:
    - stage:
        name: build
        type: CI
    - stage:
        name: deploy
        type: CD
"""
            },
            metadata={
                "category": "pipeline_creation",
                "complexity": "medium",
            },
        ),
        DatasetItem(
            id="test_2",
            input={
                "prompt": "Create a dashboard showing deployment metrics",
                "entity_type": "dashboard",
                "operation_type": "create",
            },
            expected={
                "yaml": """
dashboard:
  name: deployment-metrics
  tiles:
    - tile:
        title: Success Rate
        visualization: line_chart
"""
            },
            metadata={
                "category": "dashboard_creation",
                "complexity": "simple",
            },
        ),
    ]
    
    # ============================================================
    # 4. Run Evaluation
    # ============================================================
    
    print("Running SSE streaming evaluation...")
    print("-" * 80)
    
    # Combine all scorers: YAML quality + performance metrics
    all_scorers = [
        yaml_quality_scorer,  # Scores YAML correctness
        latency_scorer,       # Scores response time
        tool_scorer,          # Analyzes tool usage
        token_scorer,         # Tracks token consumption
    ]
    
    result = await run_evaluation(
        dataset=dataset,
        adapter=adapter,
        scorers=all_scorers,
        model="gpt-4o",
        experiment_name="sse_streaming_demo",
    )
    
    # ============================================================
    # 5. Analyze Results
    # ============================================================
    
    print("\nEvaluation Results:")
    print("=" * 80)
    
    # Group scores by test case
    scores_by_test = {}
    for score in result.scores:
        test_id = score.metadata.get("test_id", "unknown")
        if test_id not in scores_by_test:
            scores_by_test[test_id] = []
        scores_by_test[test_id].append(score)
    
    # Display results for each test case
    for test_id, scores in scores_by_test.items():
        print(f"\nTest Case: {test_id}")
        print("-" * 80)
        
        for score in scores:
            print(f"  {score.name}: {score.value:.3f}")
            if score.comment:
                print(f"    Comment: {score.comment}")
            
            # Display enriched metadata
            if "latency_ms" in score.metadata:
                print(f"    Latency: {score.metadata['latency_ms']}ms")
            if "total_tokens" in score.metadata:
                print(f"    Tokens: {score.metadata['total_tokens']}")
            if "tools_called" in score.metadata and score.metadata["tools_called"]:
                tools = [t.get("tool") for t in score.metadata["tools_called"]]
                print(f"    Tools: {tools}")
    
    # ============================================================
    # 6. Summary Statistics
    # ============================================================
    
    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    
    # Average scores by scorer type
    score_averages = {}
    for score in result.scores:
        if score.name not in score_averages:
            score_averages[score.name] = []
        if isinstance(score.value, (int, float)):
            score_averages[score.name].append(score.value)
    
    for scorer_name, values in score_averages.items():
        avg = sum(values) / len(values) if values else 0
        print(f"{scorer_name}: {avg:.3f} (avg)")
    
    # Performance metrics summary
    all_latencies = [
        s.metadata.get("latency_ms", 0)
        for s in result.scores
        if "latency_ms" in s.metadata
    ]
    if all_latencies:
        print(f"\nLatency Range: {min(all_latencies)}ms - {max(all_latencies)}ms")
    
    all_tokens = [
        s.metadata.get("total_tokens", 0)
        for s in result.scores
        if "total_tokens" in s.metadata
    ]
    if all_tokens:
        print(f"Token Range: {min(all_tokens)} - {max(all_tokens)}")
    
    print("\n" + "=" * 80)


# ============================================================
# When to Use SSE Streaming Adapter vs HTTP Adapter
# ============================================================
"""
Use SSEStreamingAdapter when:
- Your API streams responses via Server-Sent Events (SSE)
- You want to capture all intermediate events, not just final output
- You need to analyze tool calls during generation
- You want to track performance metrics (latency, tokens)
- You need to debug agent behavior by examining event sequences

Use HTTPAdapter when:
- Your API returns complete responses in a single JSON payload
- You only need the final output, not intermediate steps
- Your API doesn't support streaming

Key Benefits of SSE Streaming:
1. Complete visibility into generation process
2. Tool call analysis for debugging and validation
3. Performance metrics collection
4. Event sequence analysis
5. Backward compatible with existing scorers (via EnrichedOutputScorer)

How Enriched Output Works:
The SSEStreamingAdapter returns JSON with:
{
    "final_yaml": "...",           # Final output for YAML scorers
    "events": [...],               # All SSE events with timestamps
    "tools_called": [...],         # Tool calls with parameters
    "metrics": {                   # Performance metrics
        "latency_ms": 1234,
        "total_tokens": 500,
        ...
    }
}

EnrichedOutputScorer extracts "final_yaml" for existing scorers
while enriching metadata with metrics for analysis.
"""


if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())
