"""Utility functions for tools."""

from typing import Any

from aieval.agents.tools.base import ToolResult
from aieval.agents.tools.registry import get_tool_registry


async def execute_tool(tool_name: str, **kwargs: Any) -> ToolResult:
    """
    Execute a tool by name.

    Convenience function for executing tools directly.

    Args:
        tool_name: Name of the tool to execute
        **kwargs: Tool parameters

    Returns:
        ToolResult with execution result

    Example:
        result = await run_tool("load_dataset", dataset_type="jsonl", path="data.jsonl")
        if result.success:
            dataset = result.data["dataset"]
    """
    registry = get_tool_registry()
    tool = registry.get(tool_name)

    if tool is None:
        return ToolResult(
            success=False,
            data=None,
            error=f"Tool '{tool_name}' not found",
        )

    return await tool.execute(**kwargs)
