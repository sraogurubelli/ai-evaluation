"""Conversational agent for natural language interaction."""

from typing import Any
import structlog

from aieval.agents.base import BaseEvaluationAgent
from aieval.agents.tools import get_tool_registry, run_tool
from aieval.llm import LLMClient, LLMConfig

logger = structlog.get_logger(__name__)


class ConversationalAgent(BaseEvaluationAgent):
    """
    Conversational agent that uses LLM function calling to execute tools.

    Users interact via natural language, and the agent translates requests
    into tool calls using LLM function calling.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        llm_config: LLMConfig | None = None,
    ):
        """
        Initialize conversational agent.

        Args:
            config: Agent configuration
            llm_config: LLM configuration (uses from_env() if None)
        """
        super().__init__(config)
        self.tool_registry = get_tool_registry()

        # Initialize LLM client (may raise ImportError if LiteLLM not available)
        try:
            self.llm_client = LLMClient(llm_config)
        except ImportError as e:
            self.llm_client = None
            logger.warning(
                "LLM client not available. Conversational features disabled.",
                error=str(e),
            )

    async def chat(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Chat with the agent using natural language.

        Args:
            user_input: User's natural language input
            context: Optional conversation context

        Returns:
            Agent's natural language response
        """
        if self.llm_client is None:
            return (
                "LLM client is not available. "
                "Install with: pip install 'ai-evolution[conversational]' or pip install litellm"
            )

        # Get tool schemas for LLM
        tool_schemas = self.tool_registry.get_schemas()

        # Build messages
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant for running AI evaluations. "
                    "You can help users load datasets, create scorers, run evaluations, "
                    "compare runs, and manage baselines. "
                    "Use the available tools to accomplish tasks. "
                    "Be concise and helpful."
                ),
            },
        ]

        # Add context if provided
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Context: {context}",
                }
            )

        # Add user input
        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        # Call LLM with tools
        try:
            response = await self.llm_client.chat(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            return f"I encountered an error: {str(e)}. Please try again."

        # Handle tool calls
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]

            # Check for tool calls
            if hasattr(choice, "message") and hasattr(choice.message, "tool_calls"):
                tool_calls = choice.message.tool_calls
                if tool_calls:
                    # Execute tool calls
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        import json

                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except Exception:
                            tool_args = {}

                        # Execute tool
                        result = await run_tool(tool_name, **tool_args)
                        tool_results.append(
                            {
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "result": result.to_dict(),
                            }
                        )

                    # Send tool results back to LLM for final response
                    messages.append(choice.message)
                    for tool_result in tool_results:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_result["tool_call_id"],
                                "content": str(tool_result["result"]),
                            }
                        )

                    # Get final response
                    final_response = await self.llm_client.chat(
                        messages=messages,
                        tools=tool_schemas if tool_schemas else None,
                    )

                    if hasattr(final_response, "choices") and final_response.choices:
                        final_choice = final_response.choices[0]
                        if hasattr(final_choice, "message"):
                            return final_choice.message.content or "Task completed."
                    return "Task completed."

            # No tool calls - return direct response
            if hasattr(choice, "message"):
                return choice.message.content or "I'm here to help!"

        return "I'm here to help!"

    async def run(self, query: str, **kwargs: Any) -> Any:
        """
        Run agent with query (implements BaseEvaluationAgent interface).

        Args:
            query: Natural language query
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        context = kwargs.get("context")
        return await self.chat(query, context=context)
