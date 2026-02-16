"""Base Tool interface for evaluation agents."""

from abc import ABC, abstractmethod
from typing import Any
import json
import jsonschema
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution."""
    
    success: bool
    data: Any
    error: str | None = None
    metadata: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "data": self.data,
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class Tool(ABC):
    """
    Base class for all tools.
    
    Tools are atomic operations that can be executed directly or via LLM function calling.
    Each tool has a name, description, parameter schema, and execute method.
    """
    
    def __init__(self, name: str, description: str, parameters_schema: dict[str, Any]):
        """
        Initialize tool.
        
        Args:
            name: Tool identifier (must be unique)
            description: Tool description (for LLM function calling)
            parameters_schema: JSON schema for tool parameters
        """
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self._validate_schema()
    
    def _validate_schema(self) -> None:
        """Validate that parameters_schema is a valid JSON schema."""
        try:
            jsonschema.Draft7Validator.check_schema(self.parameters_schema)
        except jsonschema.SchemaError as e:
            raise ValueError(f"Invalid JSON schema for tool {self.name}: {e}")
    
    def validate_parameters(self, **kwargs: Any) -> None:
        """
        Validate tool parameters against schema.
        
        Args:
            **kwargs: Parameters to validate
            
        Raises:
            jsonschema.ValidationError: If parameters don't match schema
        """
        validator = jsonschema.Draft7Validator(self.parameters_schema)
        validator.validate(kwargs)
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters (validated against schema)
            
        Returns:
            ToolResult with execution result
        """
        pass
    
    def get_schema_for_llm(self) -> dict[str, Any]:
        """
        Get tool schema in format suitable for LLM function calling.
        
        Returns:
            Dictionary with name, description, and parameters
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
