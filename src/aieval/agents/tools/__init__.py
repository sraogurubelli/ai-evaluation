"""Tools system for evaluation agents."""

from aieval.agents.tools.base import Tool, ToolResult
from aieval.agents.tools.registry import ToolRegistry, get_tool_registry
from aieval.agents.tools.dataset_tools import LoadDatasetTool
from aieval.agents.tools.scorer_tools import CreateScorerTool
from aieval.agents.tools.eval_tools import CreateEvalTool, EvalTool
from aieval.agents.tools.comparison_tools import CompareEvalResultsTool
from aieval.agents.tools.baseline_tools import (
    SetBaselineTool,
    GetBaselineTool,
    get_baseline_manager,
)
from aieval.agents.tools.online_tools import (
    EvaluateTraceTool,
    EvaluateTracesTool,
    ConvertTracesToDatasetTool,
    MonitorTracesTool,
    CollectFeedbackTool,
)
from aieval.agents.tools.utils import execute_tool

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "get_tool_registry",
    "LoadDatasetTool",
    "CreateScorerTool",
    "CreateEvalTool",
    "EvalTool",
    "CompareEvalResultsTool",
    "SetBaselineTool",
    "GetBaselineTool",
    "get_baseline_manager",
    "EvaluateTraceTool",
    "EvaluateTracesTool",
    "ConvertTracesToDatasetTool",
    "MonitorTracesTool",
    "CollectFeedbackTool",
    "execute_tool",
]


def register_builtin_tools(registry: ToolRegistry | None = None) -> None:
    """
    Register all built-in tools with the registry.

    Args:
        registry: ToolRegistry instance (uses get_tool_registry() if None)
    """
    if registry is None:
        registry = get_tool_registry()

    # Register all built-in tools
    registry.register(LoadDatasetTool())
    registry.register(CreateScorerTool())
    registry.register(CreateEvalTool())
    registry.register(EvalTool())
    registry.register(CompareEvalResultsTool())
    registry.register(SetBaselineTool())
    registry.register(GetBaselineTool())
    # Online evaluation tools
    registry.register(EvaluateTraceTool())
    registry.register(EvaluateTracesTool())
    registry.register(ConvertTracesToDatasetTool())
    registry.register(MonitorTracesTool())
    registry.register(CollectFeedbackTool())
