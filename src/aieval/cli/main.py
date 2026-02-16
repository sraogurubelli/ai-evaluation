"""CLI entry point for AI Evolution Platform."""

import os
import time
import asyncio
from pathlib import Path
from typing import Any

import typer
import yaml

# Initialize logging
from aieval.logging_config import initialize_logging
import structlog

initialize_logging()
logger = structlog.get_logger(__name__)

from aieval.core.eval import Eval
from aieval.core.types import DatasetItem
from aieval.datasets import load_jsonl_dataset, load_index_csv_dataset, FunctionDataset
from aieval.adapters.http import HTTPAdapter
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer
from aieval.scorers.dashboard import DashboardQualityScorer
from aieval.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from aieval.sinks.stdout import StdoutSink
from aieval.sinks.csv import CSVSink
from aieval.sinks.json import JSONSink
from aieval.sinks.langfuse import LangfuseSink

app = typer.Typer(help="Unified agent evaluation (Eval, EvalResult, Data Set, Scores).")


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
        # Function-based dataset — not yet implemented (see docs/cleanup-audit.md)
        raise NotImplementedError(
            "Function-based datasets not yet implemented. Use jsonl or index_csv. See docs/cleanup-audit.md."
        )
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
        
        elif scorer_type == "llm_judge":
            from aieval.scorers.llm_judge import LLMJudgeScorer
            
            model = scorer_config.get("model", "gpt-4o-mini")
            rubric = scorer_config.get("rubric")
            api_key = scorer_config.get("api_key")
            
            scorer = LLMJudgeScorer(
                model=model,
                rubric=rubric,
                api_key=api_key,
            )
            scorers.append(scorer)
        
        elif scorer_type == "exact_match":
            from aieval.scorers.deterministic import ExactMatchScorer
            
            name = scorer_config.get("name", "exact_match")
            eval_id = scorer_config.get("eval_id", "exact_match.v1")
            case_sensitive = scorer_config.get("case_sensitive", False)
            normalize_whitespace = scorer_config.get("normalize_whitespace", True)
            
            scorer = ExactMatchScorer(
                name=name,
                eval_id=eval_id,
                case_sensitive=case_sensitive,
                normalize_whitespace=normalize_whitespace,
            )
            scorers.append(scorer)
        
        elif scorer_type == "contains":
            from aieval.scorers.deterministic import ContainsScorer
            
            name = scorer_config.get("name", "contains")
            eval_id = scorer_config.get("eval_id", "contains.v1")
            case_sensitive = scorer_config.get("case_sensitive", False)
            
            scorer = ContainsScorer(
                name=name,
                eval_id=eval_id,
                case_sensitive=case_sensitive,
            )
            scorers.append(scorer)
        
        elif scorer_type == "regex":
            from aieval.scorers.deterministic import RegexScorer
            
            name = scorer_config.get("name", "regex")
            eval_id = scorer_config.get("eval_id", "regex.v1")
            pattern = scorer_config.get("pattern")
            
            scorer = RegexScorer(
                name=name,
                eval_id=eval_id,
                pattern=pattern,
            )
            scorers.append(scorer)
        
        else:
            raise ValueError(f"Unknown scorer type: {scorer_type}")
    
    return scorers


def _create_adapter(config: dict[str, Any]):
    """Create adapter based on config."""
    adapter_config = config.get("adapter", {})
    adapter_type = adapter_config.get("type", "http")  # Default to http adapter
    
    if adapter_type == "function":
        from aieval.adapters.function import FunctionAdapter
        import importlib
        
        function_path = adapter_config.get("function")
        if not function_path:
            raise ValueError("function adapter requires 'function' config key (format: 'module.path:function_name')")
        
        # Parse module:function format
        if ":" not in function_path:
            raise ValueError(
                f"Invalid function path: {function_path}. "
                "Expected format: module.path:function_name"
            )
        
        module_path, function_name = function_path.rsplit(":", 1)
        
        # Import module and get function
        try:
            module = importlib.import_module(module_path)
            fn = getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import function {function_path}: {e}") from e
        
        # Create adapter with optional context
        context = adapter_config.get("context", {})
        return FunctionAdapter(fn=fn, context=context)
    
    elif adapter_type == "http" or adapter_type == "rest":
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
            context_field_name="context",
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
            name = config.get("eval", config.get("experiment", {})).get("name", "eval")
            path = path.replace("{eval_name}", name).replace("{experiment_name}", name)
            path = path.replace("{timestamp}", str(int(time.time())))
            sinks.append(CSVSink(path))

        elif sink_type == "json":
            path = sink_config.get("path", "results/results.json")
            name = config.get("eval", config.get("experiment", {})).get("name", "eval")
            path = path.replace("{eval_name}", name).replace("{experiment_name}", name)
            path = path.replace("{timestamp}", str(int(time.time())))
            sinks.append(JSONSink(path))
        
        elif sink_type == "langfuse":
            sinks.append(LangfuseSink(
                project=sink_config.get("project", "ai-evolution"),
            ))
        
        elif sink_type == "junit":
            from aieval.sinks.junit import JUnitSink
            
            path = sink_config.get("path", "results/junit.xml")
            testsuite_name = sink_config.get("testsuite_name", "aieval")
            
            sinks.append(JUnitSink(path, testsuite_name=testsuite_name))
        
        else:
            raise ValueError(f"Unknown sink type: {sink_type}")
    
    return sinks


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML config file"),
    model: str | None = typer.Option(None, "--model", "-m", help="[Deprecated] Override model from config (use --models instead)"),
    models: str | None = typer.Option(None, "--models", help="Comma-separated list of models to evaluate (e.g., 'claude-3-7-sonnet,gpt-4o')"),
    use_tools: bool = typer.Option(False, "--use-tools", help="Use tools system (experimental)"),
):
    """Run an eval from config file (config key: experiment)."""
    # Load config
    config_dict = _load_config(config)
    
    if use_tools:
        # Use tools system (experimental)
        from aieval.agents.tools import EvalTool
        
        eval_config = config_dict.get("eval", config_dict.get("experiment", {}))
        eval_name = eval_config.get("name", "eval")
        
        # Get models list
        if models:
            model_list = [m.strip() for m in models.split(",") if m.strip()]
        elif model:
            model_list = [model]
        else:
            model_list = config_dict.get("models", [])
            if not model_list:
                model_list = [None]
        
        execution_config = config_dict.get("execution", {})
        concurrency_limit = execution_config.get("concurrency_limit", 5)
        
        tool = EvalTool()
        eval_results = []
        
        for model_name in model_list:
            print(f"\nRunning eval with model: {model_name or 'default'}")
            result = asyncio.run(
                tool.execute(
                    eval_name=eval_name,
                    dataset_config=config_dict.get("dataset", {}),
                    scorers_config=config_dict.get("scorers", []),
                    adapter_config=config_dict.get("adapter", {}),
                    model=model_name,
                    concurrency_limit=concurrency_limit,
                )
            )
            
            if not result.success:
                typer.echo(f"Error: {result.error}", err=True)
                raise typer.Exit(1)
            
            # Convert result back to Run object for sinks
            from aieval.core.types import EvalResult, Score
            from datetime import datetime
            run_data = result.data["run"]
            run_obj = EvalResult(
                eval_id=run_data["eval_id"],
                run_id=run_data["run_id"],
                dataset_id=run_data["dataset_id"],
                scores=[Score(**s) for s in run_data.get("scores", [])],
                metadata=run_data.get("metadata", {}),
                created_at=datetime.fromisoformat(run_data["created_at"]) if isinstance(run_data.get("created_at"), str) else run_data.get("created_at", datetime.now()),
            )
            
            # Emit to sinks
            sinks = _create_sinks(config_dict)
            for sink in sinks:
                sink.emit_run(run_obj)
                sink.flush()
            
            run_results.append(run_obj)
            print(f"Eval run completed: {run_obj.run_id}")
        
        # If multiple models, show comparison
        if len(run_results) > 1:
            print("\n" + "="*60)
            print("MODEL COMPARISON")
            print("="*60)
            from aieval.sdk.comparison import compare_multiple_runs
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
        
        print("\nEval completed!")
    else:
        # Original implementation (backward compatible)
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
        
        # Create eval (config key: eval, or experiment for backward compatibility)
        eval_config = config_dict.get("eval", config_dict.get("experiment", {}))
        eval_name = eval_config.get("name", "eval")
        eval_ = Eval(
            name=eval_name,
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
                eval_.run(
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
            print(f"Eval run completed: {run_result.run_id}")
        
        # If multiple models, show comparison
        if len(run_results) > 1:
            print("\n" + "="*60)
            print("MODEL COMPARISON")
            print("="*60)
            from aieval.sdk.comparison import compare_multiple_runs
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
        
        print("\nEval completed!")


@app.command()
def compare(
    run1_id: str = typer.Option(..., "--run1", help="First run ID"),
    run2_id: str = typer.Option(..., "--run2", help="Second run ID"),
    use_tools: bool = typer.Option(False, "--use-tools", help="Use tools system (experimental)"),
):
    """Compare two runs."""
    if use_tools:
        # Use tools system
        from aieval.agents.tools import CompareEvalResultsTool
        
        # Note: This requires run storage to load runs by ID
        # For now, this is a placeholder
        typer.echo("Compare with tools requires run storage. See docs/cleanup-audit.md for status.")
        raise NotImplementedError("Compare command requires run storage")
    else:
        typer.echo("Compare command not yet implemented. See docs/cleanup-audit.md for status.")
        raise NotImplementedError("Compare command requires run storage")


@app.command()
def chat(
    message: str | None = typer.Option(None, "--message", "-m", help="Single message to send (non-interactive mode)"),
    model: str | None = typer.Option(None, "--model", help="LLM model to use"),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Disable interactive mode"),
):
    """Chat with the evaluation agent using natural language."""
    try:
        from aieval.agents.conversational import ConversationalAgent
        from aieval.llm import LLMConfig
    except ImportError as e:
        typer.echo(
            f"Conversational interface requires LiteLLM. Install with: pip install 'ai-evolution[conversational]' or pip install litellm",
            err=True,
        )
        raise typer.Exit(1)
    
    # Initialize agent
    llm_config = None
    if model:
        llm_config = LLMConfig(model=model)
    
    agent = ConversationalAgent(llm_config=llm_config)
    
    if message:
        # Single message mode
        result = asyncio.run(agent.chat(message))
        typer.echo(result)
    else:
        # Interactive mode
        typer.echo("Conversational Agent - Type 'exit' or 'quit' to end")
        typer.echo("=" * 60)
        
        while True:
            try:
                user_input = typer.prompt("\nYou")
                if user_input.lower() in ("exit", "quit", "q"):
                    typer.echo("Goodbye!")
                    break
                
                if not user_input.strip():
                    continue
                
                typer.echo("\nAgent:")
                result = asyncio.run(agent.chat(user_input))
                typer.echo(result)
            except KeyboardInterrupt:
                typer.echo("\n\nGoodbye!")
                break
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)


@app.command()
def evaluate_trace(
    trace_id: str = typer.Option(..., "--trace-id", help="Trace ID to evaluate"),
    trace_source: str = typer.Option("langfuse", "--source", help="Trace source (langfuse, otel)"),
    scorers: str = typer.Option(..., "--scorers", help="Comma-separated list of scorer types"),
    config: str | None = typer.Option(None, "--config", "-c", help="Path to config file with scorer configs"),
):
    """Evaluate a single production trace."""
    try:
        from aieval.agents.tools import EvaluateTraceTool
        
        # Parse scorers (simplified - in practice would load from config)
        scorer_configs = []
        for scorer_type in scorers.split(","):
            scorer_configs.append({"scorer_type": scorer_type.strip()})
        
        tool = EvaluateTraceTool()
        result = asyncio.run(
            tool.execute(
                trace_id=trace_id,
                trace_source=trace_source,
                scorers_config=scorer_configs,
            )
        )
        
        if not result.success:
            typer.echo(f"Error: {result.error}", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"Evaluation completed: {result.data['run_id']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def collect_feedback(
    trace_id: str | None = typer.Option(None, "--trace-id", help="Trace ID"),
    run_id: str | None = typer.Option(None, "--run-id", help="Run ID"),
    rating: int | None = typer.Option(None, "--rating", help="Rating (1-5)"),
    thumbs_up: bool | None = typer.Option(None, "--thumbs-up/--thumbs-down", help="Thumbs up/down"),
    comment: str | None = typer.Option(None, "--comment", help="Comment"),
):
    """Collect user feedback for a trace or run."""
    try:
        from aieval.agents.tools import CollectFeedbackTool
        
        if not trace_id and not run_id:
            typer.echo("Error: Either --trace-id or --run-id must be provided", err=True)
            raise typer.Exit(1)
        
        if not rating and thumbs_up is None:
            typer.echo("Error: Either --rating or --thumbs-up/--thumbs-down must be provided", err=True)
            raise typer.Exit(1)
        
        tool = CollectFeedbackTool()
        result = asyncio.run(
            tool.execute(
                trace_id=trace_id,
                run_id=run_id,
                rating=rating,
                thumbs_up=thumbs_up,
                comment=comment,
            )
        )
        
        if not result.success:
            typer.echo(f"Error: {result.error}", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"Feedback collected: {result.data['feedback_id']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
