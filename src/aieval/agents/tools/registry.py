"""Tool registry for managing and discovering tools."""

from typing import Any
import structlog

from aieval.agents.tools.base import Tool

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing tools.
    
    Provides singleton pattern for global tool access.
    """
    
    _instance: "ToolRegistry | None" = None
    
    def __init__(self):
        """Initialize tool registry."""
        if ToolRegistry._instance is not None:
            raise RuntimeError("ToolRegistry is a singleton. Use get_tool_registry() instead.")
        self._tools: dict[str, Tool] = {}
        self.logger = structlog.get_logger(__name__)
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If tool with same name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        self.logger.info("Tool registered", tool_name=tool.name)
    
    def get(self, name: str) -> Tool | None:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def list_all(self) -> list[Tool]:
        """
        List all registered tools.
        
        Returns:
            List of all registered tools
        """
        return list(self._tools.values())
    
    def get_schemas(self) -> list[dict[str, Any]]:
        """
        Get JSON schemas for all tools (for LLM function calling).
        
        Returns:
            List of tool schemas in LLM format
        """
        return [tool.get_schema_for_llm() for tool in self._tools.values()]
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.info("Tool unregistered", tool_name=name)
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self.logger.info("All tools cleared")


def get_tool_registry() -> ToolRegistry:
    """
    Get singleton ToolRegistry instance.
    
    Automatically registers built-in tools on first access.
    
    Returns:
        ToolRegistry instance
    """
    if ToolRegistry._instance is None:
        ToolRegistry._instance = ToolRegistry()
        # Auto-register built-in tools
        from aieval.agents.tools import register_builtin_tools
        register_builtin_tools(ToolRegistry._instance)
    return ToolRegistry._instance
