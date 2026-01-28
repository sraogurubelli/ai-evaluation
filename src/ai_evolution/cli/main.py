"""CLI entry point for AI Evolution Platform."""

import os
import time
import asyncio
from pathlib import Path
from typing import Any

import typer
import yaml

from ai_evolution.core.experiment import Experiment
from ai_evolution.core.types import DatasetItem
from ai_evolution.datasets import load_jsonl_dataset, load_index_csv_dataset, FunctionDataset
from ai_evolution.adapters.http import HTTPAdapter
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.scorers.schema_validation import SchemaValidationScorer
from ai_evolution.scorers.dashboard import DashboardQualityScorer
from ai_evolution.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from ai_evolution.sinks.stdout import StdoutSink
from ai_evolution.sinks.csv import CSVSink
from ai_evolution.sinks.json import JSONSink
from ai_evolution.sinks.langfuse import LangfuseSink

app = typer.Typer(help="AI Evolution Platform - Unified Evaluation and Experimentation")


def _expand_env_vars(value: str) -> str:
    """Expand environment variables in string."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.getenv(var_name, value)
    return value


def _load_config(config_path: str) -> dict[str, Any]:
    """Load YAML config file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Expand environment variables recursively
    def expand_dict(d: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = expand_dict(v)
            elif isinstance(v, list):
                result[k] = [expand_dict(item) if isinstance(item, dict) else _expand_env_vars(str(item)) for item in v]
            elif isinstance(v, str):
                result[k] = _expand_env_vars(v)
            else:
                result[k] = v
        return result
    
    return expand_dict(config)


def _load_dataset(config: dict[str, Any]) -> list[DatasetItem]:
    """Load dataset based on config."""
    dataset_config = config.get("dataset", {})
    dataset_type = dataset_config.get("type", "jsonl")
    
    if dataset_type == "jsonl":
        path = dataset_config["path"]
        return load_jsonl_dataset(path)
    elif dataset_type == "index_csv":
        path = dataset_config["index_file"] if "index_file" in dataset_config else dataset_config["path"]
        base_dir = dataset_config.get("base_dir", "benchmarks/datasets")
        filters = dataset_config.get("filters", {})
        return load_index_csv_dataset(
            index_file=path,
            base_dir=base_dir,
            entity_type=filters.get("entity_type"),
            operation_type=filters.get("operation_type"),
            test_id=filters.get("test_id"),
            offline=dataset_config.get("offline", False),
            actual_suffix=dataset_config.get("actual_suffix", "actual"),
        )
    elif dataset_type == "function":
        # Function-based dataset
        func_path = dataset_config["path"]
        # TODO: Import and call function
        raise NotImplementedError("Function-based datasets not yet implemented")
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")


def _create_scorers(config: dict[str, Any]) -> list:
    """Create scorers based on config."""
    scorers_config = config.get("scorers", [])
    scorers = []
    
    for scorer_config in scorers_config:
        scorer_type = scorer_config.get("type")
        
        if scorer_type == "deep_diff":
            version = scorer_config.get("version", "v3")
            entity_type = scorer_config.get("entity_type")
            validation_func = scorer_config.get("validation_func")  # Optional
            
            scorer = DeepDiffScorer(
                name=f"deep_diff_{version}",
                eval_id=f"deep_diff_{version}.v1",
                version=version,
                entity_type=entity_type,
                validation_func=validation_func,
            )
            scorers.append(scorer)
        
        elif scorer_type == "schema_validation":
            validation_func = scorer_config.get("validation_func")  # Optional
            
            scorer = SchemaValidationScorer(
                validation_func=validation_func,
            )
            scorers.append(scorer)
        
        elif scorer_type == "dashboard_quality":
            scorer = DashboardQualityScorer()
            scorers.append(scorer)
        
        elif scorer_type == "kg_quality":
            scorer = KnowledgeGraphQualityScorer()
            scorers.append(scorer)
        
        else:
            raise ValueError(f"Unknown scorer type: {scorer_type}")
    
    return scorers


def _create_adapter(config: dict[str, Any]):
    """Create adapter based on config."""
    adapter_config = config.get("adapter", {})
    adapter_type = adapter_config.get("type", "http")  # Default to http adapter
    
    if adapter_type == "http" or adapter_type == "rest":
        # Generic HTTP adapter (recommended)
        return HTTPAdapter(
            base_url=adapter_config.get("base_url", os.getenv("CHAT_BASE_URL", "http://localhost:8000")),
            auth_token=adapter_config.get("auth_token", os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")),
            context_field_name=adapter_config.get("context_field_name", "context"),
            context_data=adapter_config.get("context_data", {}),
            endpoint_mapping=adapter_config.get("endpoint_mapping", {}),
            default_endpoint=adapter_config.get("default_endpoint", "/chat/platform"),
            response_format=adapter_config.get("response_format", "json"),
            yaml_extraction_path=adapter_config.get("yaml_extraction_path"),
            sse_completion_events=adapter_config.get("sse_completion_events"),
        )
    elif adapter_type == "ml_infra":
        # Deprecated: Use "http" adapter type with ml-infra configuration
        import warnings
        warnings.warn(
            "ml_infra adapter type is deprecated. Use 'http' adapter type instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Use HTTPAdapter with ml-infra configuration
        return HTTPAdapter(
            base_url=adapter_config.get("base_url", os.getenv("CHAT_BASE_URL", "http://localhost:8000")),
            auth_token=adapter_config.get("auth_token", os.getenv("CHAT_PLATFORM_AUTH_TOKEN", "")),
            context_field_name="harness_context",
            context_data={
                "account_id": adapter_config.get("account_id", os.getenv("ACCOUNT_ID", "default")),
                "org_id": adapter_config.get("org_id", os.getenv("ORG_ID", "default")),
                "project_id": adapter_config.get("project_id", os.getenv("PROJECT_ID", "default")),
            },
            endpoint_mapping={
                "dashboard": "/chat/dashboard",
                "knowledge_graph": "/chat/knowledge-graph",
            },
            default_endpoint="/chat/platform",
            yaml_extraction_path=["capabilities_to_run", -1, "input", "yaml"],
            sse_completion_events=["dashboard_complete", "kg_complete"],
        )
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")


def _create_sinks(config: dict[str, Any]) -> list:
    """Create sinks based on config."""
    output_config = config.get("output", {})
    sinks_config = output_config.get("sinks", [])
    sinks = []
    
    for sink_config in sinks_config:
        sink_type = sink_config.get("type")
        
        if sink_type == "stdout":
            sinks.append(StdoutSink())
        
        elif sink_type == "csv":
            path = sink_config.get("path", "results/results.csv")
            # Expand placeholders
            path = path.replace("{experiment_name}", config.get("experiment", {}).get("name", "experiment"))
            path = path.replace("{timestamp}", str(int(time.time())))
            sinks.append(CSVSink(path))
        
        elif sink_type == "json":
            path = sink_config.get("path", "results/results.json")
            path = path.replace("{experiment_name}", config.get("experiment", {}).get("name", "experiment"))
            path = path.replace("{timestamp}", str(int(time.time())))
            sinks.append(JSONSink(path))
        
        elif sink_type == "langfuse":
            sinks.append(LangfuseSink(
                project=sink_config.get("project", "ai-evolution"),
            ))
        
        else:
            raise ValueError(f"Unknown sink type: {sink_type}")
    
    return sinks


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML config file"),
    model: str | None = typer.Option(None, "--model", "-m", help="[Deprecated] Override model from config (use --models instead)"),
    models: str | None = typer.Option(None, "--models", help="Comma-separated list of models to evaluate (e.g., 'claude-3-7-sonnet,gpt-4o')"),
):
    """Run an experiment from config file."""
    # Load config
    config_dict = _load_config(config)
    
    # Load dataset
    print("Loading dataset...")
    dataset = _load_dataset(config_dict)
    print(f"Loaded {len(dataset)} items")
    
    # Create scorers
    print("Creating scorers...")
    scorers = _create_scorers(config_dict)
    print(f"Created {len(scorers)} scorers: {[s.name for s in scorers]}")
    
    # Create adapter
    print("Creating adapter...")
    adapter = _create_adapter(config_dict)
    
    # Create sinks
    sinks = _create_sinks(config_dict)
    
    # Create experiment
    experiment_config = config_dict.get("experiment", {})
    experiment_name = experiment_config.get("name", "experiment")
    experiment = Experiment(
        name=experiment_name,
        dataset=dataset,
        scorers=scorers,
    )
    
    # Get models list - prioritize CLI args over config
    if models:
        # Parse comma-separated models
        model_list = [m.strip() for m in models.split(",") if m.strip()]
    elif model:
        # Backward compatibility
        model_list = [model]
    else:
        # Use config
        model_list = config_dict.get("models", [])
        if not model_list:
            model_list = [None]  # Use adapter default
    
    # Get execution config
    execution_config = config_dict.get("execution", {})
    concurrency_limit = execution_config.get("concurrency_limit", 5)
    
    # Run experiment for each model
    run_results = []
    for model_name in model_list:
        print(f"\nRunning experiment with model: {model_name or 'default'}")
        
        # Run experiment
        run_result = asyncio.run(
            experiment.run(
                adapter=adapter,
                model=model_name,
                concurrency_limit=concurrency_limit,
            )
        )
        
        # Emit to sinks
        for sink in sinks:
            sink.emit_run(run_result)
            sink.flush()
        
        run_results.append(run_result)
        print(f"Experiment run completed: {run_result.run_id}")
    
    # If multiple models, show comparison
    if len(run_results) > 1:
        print("\n" + "="*60)
        print("MODEL COMPARISON")
        print("="*60)
        from ai_evolution.sdk.comparison import compare_multiple_runs
        comparison = compare_multiple_runs(run_results, model_list)
        
        # Print scoreboard
        print("\nScoreboard (mean scores per scorer):")
        print("-" * 60)
        for scorer_name, model_data in comparison["scoreboard"].items():
            print(f"\n{scorer_name}:")
            for model_name, stats in model_data.items():
                mean = stats["mean"]
                count = stats["count"]
                print(f"  {model_name:30s}: {mean:.4f} (n={count})")
    
    print("\nExperiment completed!")


@app.command()
def compare(
    run1_id: str = typer.Option(..., "--run1", help="First run ID"),
    run2_id: str = typer.Option(..., "--run2", help="Second run ID"),
):
    """Compare two experiment runs."""
    # TODO: Load runs from storage and compare
    typer.echo("Compare command not yet implemented")
    raise NotImplementedError("Compare command requires run storage")


if __name__ == "__main__":
    app()
