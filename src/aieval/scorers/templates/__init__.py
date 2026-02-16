"""Pre-built scorer templates."""

from aieval.scorers.templates.hallucination import HallucinationScorer
from aieval.scorers.templates.helpfulness import HelpfulnessScorer
from aieval.scorers.templates.relevance import RelevanceScorer
from aieval.scorers.templates.toxicity import ToxicityScorer
from aieval.scorers.templates.correctness import CorrectnessScorer

__all__ = [
    "HallucinationScorer",
    "HelpfulnessScorer",
    "RelevanceScorer",
    "ToxicityScorer",
    "CorrectnessScorer",
]
