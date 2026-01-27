"""Scorers for evaluating AI outputs."""

from ai_evolution.scorers.base import Scorer
from ai_evolution.scorers.deep_diff import DeepDiffScorer
from ai_evolution.scorers.schema_validation import SchemaValidationScorer
from ai_evolution.scorers.dashboard import DashboardQualityScorer
from ai_evolution.scorers.knowledge_graph import KnowledgeGraphQualityScorer
from ai_evolution.scorers.llm_judge import LLMJudgeScorer

# Autoevals-style scorers (Braintrust)
try:
    from ai_evolution.scorers.autoevals import (
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

__all__ = [
    "Scorer",
    "DeepDiffScorer",
    "SchemaValidationScorer",
    "DashboardQualityScorer",
    "KnowledgeGraphQualityScorer",
    "LLMJudgeScorer",
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
