"""Skill registry for managing and discovering skills."""

from typing import Any
import structlog

from aieval.agents.skills.base import Skill

logger = structlog.get_logger(__name__)


class SkillRegistry:
    """
    Registry for managing skills.
    
    Provides singleton pattern for global skill access.
    """
    
    _instance: "SkillRegistry | None" = None
    
    def __init__(self):
        """Initialize skill registry."""
        if SkillRegistry._instance is not None:
            raise RuntimeError("SkillRegistry is a singleton. Use get_skill_registry() instead.")
        self._skills: dict[str, Skill] = {}
        self.logger = structlog.get_logger(__name__)
    
    def register(self, skill: Skill) -> None:
        """
        Register a skill.
        
        Args:
            skill: Skill instance to register
            
        Raises:
            ValueError: If skill with same name already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill with name '{skill.name}' is already registered")
        self._skills[skill.name] = skill
        self.logger.info("Skill registered", skill_name=skill.name)
    
    def get(self, name: str) -> Skill | None:
        """
        Get skill by name.
        
        Args:
            name: Skill name
            
        Returns:
            Skill instance or None if not found
        """
        return self._skills.get(name)
    
    def list_all(self) -> list[Skill]:
        """
        List all registered skills.
        
        Returns:
            List of all registered skills
        """
        return list(self._skills.values())
    
    def unregister(self, name: str) -> None:
        """
        Unregister a skill.
        
        Args:
            name: Skill name to unregister
        """
        if name in self._skills:
            del self._skills[name]
            self.logger.info("Skill unregistered", skill_name=name)
    
    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()
        self.logger.info("All skills cleared")


def get_skill_registry() -> SkillRegistry:
    """
    Get singleton SkillRegistry instance.
    
    Automatically registers built-in skills on first access.
    
    Returns:
        SkillRegistry instance
    """
    if SkillRegistry._instance is None:
        SkillRegistry._instance = SkillRegistry()
        # Auto-register built-in skills
        from aieval.agents.skills import register_builtin_skills
        register_builtin_skills(SkillRegistry._instance)
    return SkillRegistry._instance
