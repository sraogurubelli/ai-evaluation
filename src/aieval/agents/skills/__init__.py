"""Skills system for reusable workflows."""

from aieval.agents.skills.base import Skill
from aieval.agents.skills.registry import SkillRegistry, get_skill_registry
from aieval.agents.skills.evaluation_skill import EvaluationSkill
from aieval.agents.skills.baseline_comparison_skill import BaselineComparisonSkill
from aieval.agents.skills.multi_model_evaluation_skill import MultiModelEvaluationSkill

__all__ = [
    "Skill",
    "SkillRegistry",
    "get_skill_registry",
    "EvaluationSkill",
    "BaselineComparisonSkill",
    "MultiModelEvaluationSkill",
]


def register_builtin_skills(registry: SkillRegistry | None = None) -> None:
    """
    Register all built-in skills with the registry.

    Args:
        registry: SkillRegistry instance (uses get_skill_registry() if None)
    """
    if registry is None:
        registry = get_skill_registry()

    # Register all built-in skills
    registry.register(EvaluationSkill())
    registry.register(BaselineComparisonSkill())
    registry.register(MultiModelEvaluationSkill())
