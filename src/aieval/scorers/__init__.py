"""Scorers for evaluating AI outputs."""

from aieval.scorers.base import Scorer
from aieval.scorers.deep_diff import DeepDiffScorer
from aieval.scorers.schema_validation import SchemaValidationScorer
from aieval.scorers.dashboard import DashboardQualityScorer
from aieval.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from aieval.scorers.llm_judge import LLMJudgeScorer
from aieval.scorers.enriched import EnrichedOutputScorer
from aieval.scorers.metrics import LatencyScorer, ToolCallScorer, TokenUsageScorer

# Autoevals-style scorers (Braintrust)
try:
    from aieval.scorers.autoevals import (
        LLMJudgeScorer as AutoevalsLLMJudgeScorer,
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

# Guardrail scorers
try:
    from aieval.scorers.guardrails import (
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
    "Scorer",
    "DeepDiffScorer",
    "SchemaValidationScorer",
    "DashboardQualityScorer",
    "KnowledgeGraphQualityScorer",
    "LLMJudgeScorer",
    "EnrichedOutputScorer",
    "LatencyScorer",
    "ToolCallScorer",
    "TokenUsageScorer",
]

if AUTOEVALS_AVAILABLE:
    __all__.extend([
        "AutoevalsLLMJudgeScorer",
        "FactualityScorer",
        "HelpfulnessScorer",
        "LevenshteinScorer",
        "BLUEScorer",
        "EmbeddingSimilarityScorer",
        "RAGRelevanceScorer",
    ])

if GUARDRAILS_AVAILABLE:
    __all__.extend([
        "GuardrailScorer",
        "HallucinationScorer",
        "PromptInjectionScorer",
        "ToxicityScorer",
        "PIIScorer",
        "SensitiveDataScorer",
        "RegexScorer",
        "KeywordScorer",
    ])
