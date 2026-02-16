"""Base Skill interface."""

from abc import ABC, abstractmethod
from typing import Any


class Skill(ABC):
    """
    Base class for skills.

    Skills are reusable workflows that compose multiple tools or agents.
    They provide higher-level operations than individual tools.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize skill.

        Args:
            name: Skill identifier
            description: Skill description
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the skill.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            Skill execution result
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
