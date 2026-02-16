"""Component loader for auto-discovering custom tools and skills."""

import importlib
import importlib.metadata
from typing import Any
import structlog

from aieval.agents.tools import Tool, get_tool_registry
from aieval.agents.skills import Skill, get_skill_registry

logger = structlog.get_logger(__name__)


def load_tools_from_entry_points(group: str = "aieval.tools") -> None:
    """
    Load tools from entry points.

    Entry points should be defined in pyproject.toml or setup.py:
    [project.entry-points."aieval.tools"]
    my_tool = "mypackage.tools:MyTool"

    Args:
        group: Entry point group name (default: "aieval.tools")
    """
    registry = get_tool_registry()

    try:
        entry_points = importlib.metadata.entry_points(group=group)
        for entry_point in entry_points:
            try:
                tool_class = entry_point.load()
                if issubclass(tool_class, Tool):
                    tool_instance = tool_class()
                    registry.register(tool_instance)
                    logger.info(
                        "Loaded tool from entry point",
                        tool_name=tool_instance.name,
                        entry_point=entry_point.name,
                    )
                else:
                    logger.warning(
                        "Entry point does not provide a Tool subclass",
                        entry_point=entry_point.name,
                        module=entry_point.module,
                    )
            except Exception as e:
                logger.error(
                    "Failed to load tool from entry point",
                    entry_point=entry_point.name,
                    error=str(e),
                )
    except Exception as e:
        logger.warning("Failed to load entry points", group=group, error=str(e))


def load_skills_from_entry_points(group: str = "aieval.skills") -> None:
    """
    Load skills from entry points.

    Entry points should be defined in pyproject.toml or setup.py:
    [project.entry-points."aieval.skills"]
    my_skill = "mypackage.skills:MySkill"

    Args:
        group: Entry point group name (default: "aieval.skills")
    """
    registry = get_skill_registry()

    try:
        entry_points = importlib.metadata.entry_points(group=group)
        for entry_point in entry_points:
            try:
                skill_class = entry_point.load()
                if issubclass(skill_class, Skill):
                    skill_instance = skill_class()
                    registry.register(skill_instance)
                    logger.info(
                        "Loaded skill from entry point",
                        skill_name=skill_instance.name,
                        entry_point=entry_point.name,
                    )
                else:
                    logger.warning(
                        "Entry point does not provide a Skill subclass",
                        entry_point=entry_point.name,
                        module=entry_point.module,
                    )
            except Exception as e:
                logger.error(
                    "Failed to load skill from entry point",
                    entry_point=entry_point.name,
                    error=str(e),
                )
    except Exception as e:
        logger.warning("Failed to load entry points", group=group, error=str(e))


def load_all_components() -> None:
    """Load all custom components (tools and skills) from entry points."""
    load_tools_from_entry_points()
    load_skills_from_entry_points()
    logger.info("Loaded all custom components from entry points")
