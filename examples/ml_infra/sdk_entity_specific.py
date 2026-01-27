"""Example: ML Infra Entity-Specific Evaluation Patterns.

This demonstrates entity-specific evaluation patterns for different ML Infra entity types.
"""

import asyncio
from ai_evolution import (
    Experiment,
    MLInfraAdapter,
    DeepDiffScorer,
    DashboardQualityScorer,
    KnowledgeGraphQualityScorer,
    load_index_csv_dataset,
    CSVSink,
)


async def example_pipeline_evaluation():
    """Evaluate pipeline creation/update."""
    print("=== Pipeline Evaluation ===")
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="create",
    )
    
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
        DeepDiffScorer(name="deep_diff_v2", eval_id="deep_diff_v2.v1", version="v2"),
    ]
    
    experiment = Experiment(
        name="pipeline_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    adapter = MLInfraAdapter(base_url="http://localhost:8000")
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet-20250219")
    print(f"Pipeline evaluation completed: {len(result.scores)} scores")


async def example_dashboard_evaluation():
    """Evaluate dashboard creation."""
    print("\n=== Dashboard Evaluation ===")
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="dashboard",
        operation_type="create",
    )
    
    scorers = [
        DashboardQualityScorer(),
    ]
    
    experiment = Experiment(
        name="dashboard_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    adapter = MLInfraAdapter(base_url="http://localhost:8000")
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet-20250219")
    print(f"Dashboard evaluation completed: {len(result.scores)} scores")


async def example_knowledge_graph_evaluation():
    """Evaluate knowledge graph creation."""
    print("\n=== Knowledge Graph Evaluation ===")
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="knowledge_graph",
        operation_type="create",
    )
    
    scorers = [
        KnowledgeGraphQualityScorer(),
    ]
    
    experiment = Experiment(
        name="kg_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    adapter = MLInfraAdapter(base_url="http://localhost:8000")
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet-20250219")
    print(f"Knowledge Graph evaluation completed: {len(result.scores)} scores")


async def example_service_evaluation():
    """Evaluate service creation."""
    print("\n=== Service Evaluation ===")
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="service",
        operation_type="create",
    )
    
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
    ]
    
    experiment = Experiment(
        name="service_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    adapter = MLInfraAdapter(base_url="http://localhost:8000")
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet-20250219")
    print(f"Service evaluation completed: {len(result.scores)} scores")


async def example_update_operation():
    """Evaluate update operations (requires old_yaml)."""
    print("\n=== Update Operation Evaluation ===")
    
    dataset = load_index_csv_dataset(
        index_file="benchmarks/datasets/index.csv",
        base_dir="benchmarks/datasets",
        entity_type="pipeline",
        operation_type="update",  # Update operations
    )
    
    # Verify dataset items have old_yaml in input
    for item in dataset:
        if "old_yaml" not in item.input:
            print(f"Warning: Item {item.id} missing old_yaml for update operation")
    
    scorers = [
        DeepDiffScorer(name="deep_diff_v3", eval_id="deep_diff_v3.v1", version="v3"),
    ]
    
    experiment = Experiment(
        name="pipeline_update_evaluation",
        dataset=dataset,
        scorers=scorers,
    )
    
    adapter = MLInfraAdapter(base_url="http://localhost:8000")
    
    result = await experiment.run(adapter=adapter, model="claude-3-7-sonnet-20250219")
    print(f"Update operation evaluation completed: {len(result.scores)} scores")


if __name__ == "__main__":
    # Run examples (requires ml-infra server)
    print("Entity-specific evaluation examples")
    print("Uncomment to run (requires ml-infra server):")
    # asyncio.run(example_pipeline_evaluation())
    # asyncio.run(example_dashboard_evaluation())
    # asyncio.run(example_knowledge_graph_evaluation())
    # asyncio.run(example_service_evaluation())
    # asyncio.run(example_update_operation())
