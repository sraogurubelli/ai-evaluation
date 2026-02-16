"""Agent trace format and parsers for various frameworks."""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AgentStep:
    """Single step in an agent trace."""

    step_number: int
    action: str  # "llm_call", "tool_call", "reasoning", etc.
    input: dict[str, Any]
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None
    cost: float | None = None
    tokens: dict[str, int] | None = None  # {"input": 100, "output": 50}


@dataclass
class ToolCall:
    """Tool call in an agent trace."""

    id: str
    tool_name: str
    parameters: dict[str, Any]
    result: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None
    cost: float | None = None
    duration_ms: float | None = None


@dataclass
class AgentTrace:
    """Complete agent trace."""

    trace_id: str
    agent_name: str
    steps: list[AgentStep]
    tool_calls: list[ToolCall]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "agent_name": self.agent_name,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action": s.action,
                    "input": s.input,
                    "output": s.output,
                    "metadata": s.metadata,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    "cost": s.cost,
                    "tokens": s.tokens,
                }
                for s in self.steps
            ],
            "tool_calls": [
                {
                    "id": tc.id,
                    "tool_name": tc.tool_name,
                    "parameters": tc.parameters,
                    "result": tc.result,
                    "metadata": tc.metadata,
                    "timestamp": tc.timestamp.isoformat() if tc.timestamp else None,
                    "cost": tc.cost,
                    "duration_ms": tc.duration_ms,
                }
                for tc in self.tool_calls
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


def parse_langgraph_trace(trace_data: dict[str, Any]) -> AgentTrace:
    """
    Parse LangGraph trace format.

    Args:
        trace_data: LangGraph trace data

    Returns:
        AgentTrace object
    """
    trace_id = trace_data.get("trace_id") or trace_data.get("id", "")
    agent_name = trace_data.get("agent_name", "langgraph_agent")

    steps = []
    tool_calls = []

    # Parse LangGraph steps
    langgraph_steps = trace_data.get("steps", []) or trace_data.get("events", [])

    for i, step_data in enumerate(langgraph_steps):
        step_type = step_data.get("type") or step_data.get("event_type", "")

        if step_type in ("tool", "tool_call"):
            # Tool call
            tool_call = ToolCall(
                id=step_data.get("id", f"tool_{i}"),
                tool_name=step_data.get("tool_name") or step_data.get("name", ""),
                parameters=step_data.get("parameters", {}) or step_data.get("input", {}),
                result=step_data.get("result") or step_data.get("output"),
                metadata=step_data.get("metadata", {}),
                timestamp=datetime.fromisoformat(step_data["timestamp"])
                if step_data.get("timestamp")
                else None,
            )
            tool_calls.append(tool_call)

        # Create step
        step = AgentStep(
            step_number=i + 1,
            action=step_type or "unknown",
            input=step_data.get("input", {}) or step_data.get("data", {}),
            output=step_data.get("output") or step_data.get("result"),
            metadata=step_data.get("metadata", {}),
            timestamp=datetime.fromisoformat(step_data["timestamp"])
            if step_data.get("timestamp")
            else None,
        )
        steps.append(step)

    return AgentTrace(
        trace_id=trace_id,
        agent_name=agent_name,
        steps=steps,
        tool_calls=tool_calls,
        metadata=trace_data.get("metadata", {}),
    )


def parse_openai_agents_trace(trace_data: dict[str, Any]) -> AgentTrace:
    """
    Parse OpenAI Agents SDK trace format.

    Args:
        trace_data: OpenAI Agents SDK trace data

    Returns:
        AgentTrace object
    """
    trace_id = trace_data.get("thread_id") or trace_data.get("id", "")
    agent_name = trace_data.get("assistant_id", "openai_agent")

    steps = []
    tool_calls = []

    # Parse OpenAI messages/steps
    messages = trace_data.get("messages", []) or trace_data.get("steps", [])

    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Check for tool calls
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_call = ToolCall(
                    id=tc.get("id", f"tool_{len(tool_calls)}"),
                    tool_name=tc.get("function", {}).get("name", ""),
                    parameters=tc.get("function", {}).get("arguments", {}),
                    result=None,  # Would be in next message
                    metadata={"role": role},
                )
                tool_calls.append(tool_call)

        # Create step
        step = AgentStep(
            step_number=i + 1,
            action=f"{role}_message",
            input={"role": role, "content": content},
            output=content,
            metadata=msg.get("metadata", {}),
        )
        steps.append(step)

    return AgentTrace(
        trace_id=trace_id,
        agent_name=agent_name,
        steps=steps,
        tool_calls=tool_calls,
        metadata=trace_data.get("metadata", {}),
    )


def parse_pydantic_ai_trace(trace_data: dict[str, Any]) -> AgentTrace:
    """
    Parse PydanticAI trace format.

    Args:
        trace_data: PydanticAI trace data

    Returns:
        AgentTrace object
    """
    trace_id = trace_data.get("trace_id") or trace_data.get("id", "")
    agent_name = trace_data.get("agent_name", "pydantic_ai_agent")

    steps = []
    tool_calls = []

    # Parse PydanticAI steps
    pydantic_steps = trace_data.get("steps", []) or trace_data.get("events", [])

    for i, step_data in enumerate(pydantic_steps):
        step_type = step_data.get("type", "step")

        # Check for tool calls
        if step_data.get("tool_calls"):
            for tc in step_data["tool_calls"]:
                tool_call = ToolCall(
                    id=tc.get("id", f"tool_{len(tool_calls)}"),
                    tool_name=tc.get("name", ""),
                    parameters=tc.get("arguments", {}),
                    result=tc.get("result"),
                    metadata=tc.get("metadata", {}),
                )
                tool_calls.append(tool_call)

        # Create step
        step = AgentStep(
            step_number=i + 1,
            action=step_type,
            input=step_data.get("input", {}),
            output=step_data.get("output") or step_data.get("result"),
            metadata=step_data.get("metadata", {}),
        )
        steps.append(step)

    return AgentTrace(
        trace_id=trace_id,
        agent_name=agent_name,
        steps=steps,
        tool_calls=tool_calls,
        metadata=trace_data.get("metadata", {}),
    )
