"""AI Evolution SDK - Public API for customers.

This SDK provides a clean, customer-friendly interface for:
- Running evaluations
- Creating custom scorers
- Managing datasets
- Integrating with AI systems

Usage:
    from ai_evolution import Experiment, HTTPAdapter, DeepDiffScorer
    
    # Create experiment
    experiment = Experiment(
        name="my_eval",
        dataset=load_dataset("dataset.jsonl"),
        scorers=[DeepDiffScorer(...)]
    )
    
    # Run evaluation
    result = await experiment.run(adapter=HTTPAdapter(...), model="gpt-4o")
"""

# Core types
from ai_evolution.core.types import DatasetItem, ExperimentRun, Score

# Experiment system
from ai_evolution.core.experiment import Experiment

# Adapters
from ai_evolution.adapters import HTTPAdapter, LangfuseAdapter, Adapter

# Scorers
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.scorers.schema_validation import SchemaValidationScorer
from ai_evolution.scorers.dashboard import DashboardQualityScorer
from ai_evolution.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from ai_evolution.scorers.base import Scorer

# Autoevals-style scorers (Braintrust)
try:
    from ai_evolution.scorers.autoevals import (
        FactualityScorer,
        HelpfulnessScorer,
        LevenshteinScorer,
        BLUEScorer,
        EmbeddingSimilarityScorer,
        RAGRelevanceScorer,
    )
    AUTOEVALS_AVAILABLE = True
except ImportError:
    AUTOEVALS_AVAILABLE = False

# Dataset loaders
from ai_evolution.datasets.jsonl import load_jsonl_dataset
from ai_evolution.datasets.index_csv import load_index_csv_dataset
from ai_evolution.datasets.function import FunctionDataset

# Sinks
from ai_evolution.sinks.stdout import StdoutSink
from ai_evolution.sinks.csv import CSVSink
from ai_evolution.sinks.json import JSONSink
from ai_evolution.sinks.langfuse import LangfuseSink
from ai_evolution.sinks.base import Sink

# Runner
from ai_evolution.sdk.runner import EvaluationRunner, run_evaluation

# Task abstraction (Braintrust-style)
from ai_evolution.sdk.task import Task, FunctionTask, AdapterTask

# Assertions (OpenAI Evals style)
from ai_evolution.sdk.assertions import (
    Assertion,
    ContainsAssertion,
    RegexAssertion,
    ExactMatchAssertion,
    JSONSchemaAssertion,
    FunctionAssertion,
    AssertionScorer,
)

# Comparison (Braintrust-style)
from ai_evolution.sdk.comparison import compare_runs, RunComparison, get_regressions

# Registry (if available)
try:
    from ai_evolution.sdk.registry import load_registry, EvalRegistryEntry
except ImportError:
    pass

# ML Infra helpers
try:
    from ai_evolution.sdk.ml_infra import (
        create_ml_infra_experiment,
        run_ml_infra_eval,
        compare_csv_results,
        create_ml_infra_sinks,
        load_single_test_case,
        score_single_output,
        run_single_test,
        verify_test_compatibility,
    )
    ML_INFRA_HELPERS_AVAILABLE = True
except ImportError:
    ML_INFRA_HELPERS_AVAILABLE = False

__all__ = [
    # Core types
    "DatasetItem",
    "ExperimentRun",
    "Score",
    # Experiment system
    "Experiment",
    # Adapters
    "HTTPAdapter",
    "LangfuseAdapter",
    "Adapter",
    # Scorers
    "DeepDiffScorer",
    "SchemaValidationScorer",
    "DashboardQualityScorer",
    "KnowledgeGraphQualityScorer",
    "Scorer",
    # Autoevals-style scorers (if available)
    *(["FactualityScorer", "HelpfulnessScorer", "LevenshteinScorer", "BLUEScorer", "EmbeddingSimilarityScorer", "RAGRelevanceScorer"] if AUTOEVALS_AVAILABLE else []),
    # Dataset loaders
    "load_jsonl_dataset",
    "load_index_csv_dataset",
    "FunctionDataset",
    # Sinks
    "StdoutSink",
    "CSVSink",
    "JSONSink",
    "LangfuseSink",
    "Sink",
    # Runner
    "EvaluationRunner",
    "run_evaluation",
    # Task abstraction
    "Task",
    "FunctionTask",
    "AdapterTask",
    # Assertions
    "Assertion",
    "ContainsAssertion",
    "RegexAssertion",
    "ExactMatchAssertion",
    "JSONSchemaAssertion",
    "FunctionAssertion",
    "AssertionScorer",
    # Comparison
    "compare_runs",
    "compare_multiple_runs",
    "RunComparison",
    "get_regressions",
    # ML Infra helpers (if available)
    *(["create_ml_infra_experiment", "run_ml_infra_eval", "compare_csv_results", "create_ml_infra_sinks", "load_single_test_case", "score_single_output", "run_single_test", "verify_test_compatibility"] if ML_INFRA_HELPERS_AVAILABLE else []),
]
