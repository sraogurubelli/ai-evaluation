"""AI Evolution SDK - Public API for customers.

This SDK provides a clean, customer-friendly interface for:
- Running evaluations
- Creating custom scorers
- Managing datasets
- Integrating with AI systems

Usage:
    from aieval import Eval, HTTPAdapter, DeepDiffScorer

    # Create eval
    eval_ = Eval(
        name="my_eval",
        dataset=load_dataset("dataset.jsonl"),
        scorers=[DeepDiffScorer(...)]
    )

    # Run evaluation
    result = await eval_.run(adapter=HTTPAdapter(...), model="gpt-4o")
"""

# Core types
from aieval.core.types import DatasetItem, EvalResult, Score

# Eval system
from aieval.core.eval import Eval

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
from aieval.sinks.junit import JUnitSink
from aieval.sinks.html_report import HTMLReportSink
from aieval.sinks.base import Sink

# Runner
from aieval.sdk.runner import EvaluationRunner, run_evaluation

# Online evaluation
from aieval.evaluation.online import OnlineEvaluationAgent
from aieval.monitoring.evaluator import ContinuousEvaluator
from aieval.feedback.collector import FeedbackCollector
from aieval.feedback.integrator import FeedbackIntegrator

# Incremental evaluation
from aieval.evaluation.incremental import IncrementalEvaluator

# Agent tracing
from aieval.tracing import (
    AgentTrace,
    parse_langgraph_trace,
    parse_openai_agents_trace,
    parse_pydantic_ai_trace,
)

# CI/CD
from aieval.ci.gates import DeploymentGate

# Scorer templates
from aieval.scorers.templates import (
    HallucinationScorer,
    HelpfulnessScorer,
    RelevanceScorer,
    ToxicityScorer,
    CorrectnessScorer,
)

# Agent scorers
from aieval.scorers.agent import (
    ToolCallAccuracyScorer,
    ParameterCorrectnessScorer,
    StepSelectionScorer,
)

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
    compare_eval_results,
    compare_multiple_eval_results,
    EvalResultComparison,
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

# Tools system
from aieval.agents.tools import (
    get_tool_registry,
    execute_tool,
    LoadDatasetTool,
    CreateScorerTool,
    CreateEvalTool,
    EvalTool,
    CompareEvalResultsTool,
    SetBaselineTool,
    GetBaselineTool,
    EvaluateTraceTool,
    EvaluateTracesTool,
    ConvertTracesToDatasetTool,
    MonitorTracesTool,
    CollectFeedbackTool,
)

__all__ = [
    # Core types
    "DatasetItem",
    "EvalResult",
    "Score",
    # Eval system
    "Eval",
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
    *(
        [
            "FactualityScorer",
            "HelpfulnessScorer",
            "LevenshteinScorer",
            "BLUEScorer",
            "EmbeddingSimilarityScorer",
            "RAGRelevanceScorer",
        ]
        if AUTOEVALS_AVAILABLE
        else []
    ),
    # Dataset loaders
    "load_jsonl_dataset",
    "load_index_csv_dataset",
    "FunctionDataset",
    # Sinks
    "StdoutSink",
    "CSVSink",
    "JSONSink",
    "LangfuseSink",
    "JUnitSink",
    "HTMLReportSink",
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
    "compare_eval_results",
    "compare_multiple_eval_results",
    "EvalResultComparison",
    "get_regressions",
    # Unit-test helpers (agent-agnostic)
    "score_single_output",
    "run_single_item",
    "assert_score_min",
    # Guardrail SDK (if available)
    *(
        [
            "validate_prompt",
            "validate_response",
            "load_policy",
            "validate_policy_config",
            "get_policy_engine",
            "GuardrailScorer",
            "HallucinationScorer",
            "PromptInjectionScorer",
            "ToxicityScorer",
            "PIIScorer",
            "SensitiveDataScorer",
            "RegexScorer",
            "KeywordScorer",
        ]
        if GUARDRAILS_AVAILABLE
        else []
    ),
    # Tools system
    "get_tool_registry",
    "execute_tool",
    "LoadDatasetTool",
    "CreateScorerTool",
    "CreateEvalTool",
    "EvalTool",
    "CompareEvalResultsTool",
    "SetBaselineTool",
    "GetBaselineTool",
    # Online evaluation
    "EvaluateTraceTool",
    "EvaluateTracesTool",
    "ConvertTracesToDatasetTool",
    "MonitorTracesTool",
    "CollectFeedbackTool",
    # Online evaluation components
    "OnlineEvaluationAgent",
    "ContinuousEvaluator",
    "FeedbackCollector",
    "FeedbackIntegrator",
    # Incremental evaluation
    "IncrementalEvaluator",
    # Agent tracing
    "AgentTrace",
    "parse_langgraph_trace",
    "parse_openai_agents_trace",
    "parse_pydantic_ai_trace",
    # CI/CD
    "DeploymentGate",
    # Scorer templates
    "HallucinationScorer",
    "HelpfulnessScorer",
    "RelevanceScorer",
    "ToxicityScorer",
    "CorrectnessScorer",
    # Agent scorers
    "ToolCallAccuracyScorer",
    "ParameterCorrectnessScorer",
    "StepSelectionScorer",
]
