"""AI Evolution - Unified AI Evaluation and Experimentation Platform.

This package provides:
- SDK: Clean public API for customers (import from ai_evolution.sdk)
- Core: Experiment system, types, scorers
- Adapters: AI system integrations
- CLI: Command-line interface
- API: REST API server
"""

# Re-export SDK for convenience (customer-friendly API)
# Import AUTOEVALS_AVAILABLE flag
try:
    from ai_evolution.sdk import AUTOEVALS_AVAILABLE
except ImportError:
    AUTOEVALS_AVAILABLE = False

from ai_evolution.sdk import (
    # Core types
    DatasetItem,
    ExperimentRun,
    Score,
    # Experiment system
    Experiment,
    # Adapters
    HTTPAdapter,
    
    LangfuseAdapter,
    Adapter,
    # Scorers
    DeepDiffScorer,
    SchemaValidationScorer,
    DashboardQualityScorer,
    KnowledgeGraphQualityScorer,
    Scorer,
    # Dataset loaders
    load_jsonl_dataset,
    load_index_csv_dataset,
    FunctionDataset,
    # Sinks
    StdoutSink,
    CSVSink,
    JSONSink,
    LangfuseSink,
    Sink,
    # Runner
    EvaluationRunner,
    run_evaluation,
)

__version__ = "0.1.0"

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
    "RunComparison",
    "get_regressions",
]
