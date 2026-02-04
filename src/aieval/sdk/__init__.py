"""AI Evolution SDK - Public API for customers.

This SDK provides a clean, customer-friendly interface for:
- Running evaluations
- Creating custom scorers
- Managing datasets
- Integrating with AI systems

Usage:
    from aieval import Experiment, HTTPAdapter, DeepDiffScorer
    
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
from aieval.core.types import DatasetItem, ExperimentRun, Score

# Experiment system
from aieval.core.experiment import Experiment

# Adapters
from aieval.adapters import HTTPAdapter, LangfuseAdapter, Adapter

# Scorers
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer
from aieval.scorers.dashboard import DashboardQualityScorer
from aieval.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from aieval.scorers.base import Scorer

# Autoevals-style scorers (Braintrust)
try:
    from aieval.scorers.autoevals import (
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
from aieval.datasets.jsonl import load_jsonl_dataset
from aieval.datasets.index_csv import load_index_csv_dataset
from aieval.datasets.function import FunctionDataset

# Sinks
from aieval.sinks.stdout import StdoutSink
from aieval.sinks.csv import CSVSink
from aieval.sinks.json import JSONSink
from aieval.sinks.langfuse import LangfuseSink
from aieval.sinks.base import Sink

# Runner
from aieval.sdk.runner import EvaluationRunner, run_evaluation

# Task abstraction (Braintrust-style)
from aieval.sdk.task import Task, FunctionTask, AdapterTask

# Assertions (OpenAI Evals style)
from aieval.sdk.assertions import (
    Assertion,
    ContainsAssertion,
    RegexAssertion,
    ExactMatchAssertion,
    JSONSchemaAssertion,
    FunctionAssertion,
    AssertionScorer,
)

# Comparison (Braintrust-style)
from aieval.sdk.comparison import (
    compare_runs,
    compare_multiple_runs,
    RunComparison,
    get_regressions,
)

# Registry (if available)
try:
    from aieval.sdk.registry import load_registry, EvalRegistryEntry
except ImportError:
    pass

# Agent-agnostic unit-test helpers (always available)
from aieval.sdk.unit_test import (
    score_single_output,
    run_single_item,
    assert_score_min,
)

# Guardrail SDK
try:
    from aieval.sdk.guardrails import (
        validate_prompt,
        validate_response,
        load_policy,
        validate_policy_config,
        get_policy_engine,
        # Scorers
        GuardrailScorer,
        HallucinationScorer,
        PromptInjectionScorer,
        ToxicityScorer,
        PIIScorer,
        SensitiveDataScorer,
        RegexScorer,
        KeywordScorer,
    )
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False

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
    # Unit-test helpers (agent-agnostic)
    "score_single_output",
    "run_single_item",
    "assert_score_min",
    # Guardrail SDK (if available)
    *(["validate_prompt", "validate_response", "load_policy", "validate_policy_config", "get_policy_engine", "GuardrailScorer", "HallucinationScorer", "PromptInjectionScorer", "ToxicityScorer", "PIIScorer", "SensitiveDataScorer", "RegexScorer", "KeywordScorer"] if GUARDRAILS_AVAILABLE else []),
]
