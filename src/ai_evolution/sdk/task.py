"""Task abstraction for evaluation (Braintrust-style).

A Task is a clean function that takes input and produces output.
This abstraction makes it easy to define what you're evaluating without
worrying about adapters, models, etc.
"""

from typing import Any, Callable, Awaitable
from abc import ABC, abstractmethod


class Task(ABC):
    """
    Abstract task interface.
    
    A task represents a function that takes input and produces output.
    This is similar to Braintrust's task abstraction.
    
    Example:
        class MyTask(Task):
            async def run(self, input: dict[str, Any]) -> Any:
                # Your LLM call or agent logic
                return await llm.generate(input["prompt"])
    """
    
    @abstractmethod
    async def run(self, input: dict[str, Any]) -> Any:
        """
        Execute the task with given input.
        
        Args:
            input: Input dictionary (typically contains prompt, context, etc.)
        
        Returns:
            Task output (string, dict, etc.)
        """
        pass


class FunctionTask(Task):
    """
    Task wrapper for a simple async function.
    
    Example:
        async def my_llm_call(input: dict[str, Any]) -> str:
            return await llm.generate(input["prompt"])
        
        task = FunctionTask(my_llm_call)
    """
    
    def __init__(self, func: Callable[[dict[str, Any]], Awaitable[Any]]):
        """
        Initialize function task.
        
        Args:
            func: Async function that takes input dict and returns output
        """
        self.func = func
    
    async def run(self, input: dict[str, Any]) -> Any:
        """Execute the function with input."""
        return await self.func(input)


class AdapterTask(Task):
    """
    Task wrapper for an adapter.
    
    This makes adapters work as tasks, providing a clean abstraction.
    
    Example:
        adapter = HTTPAdapter(base_url="http://api.com")
        task = AdapterTask(adapter, model="gpt-4o")
        
        output = await task.run({"prompt": "Hello"})
    """
    
    def __init__(self, adapter: Any, model: str | None = None, **kwargs: Any):
        """
        Initialize adapter task.
        
        Args:
            adapter: Adapter instance (HTTPAdapter, or custom adapters)
            model: Optional model name
            **kwargs: Additional arguments passed to adapter.generate()
        """
        self.adapter = adapter
        self.model = model
        self.kwargs = kwargs
    
    async def run(self, input: dict[str, Any]) -> Any:
        """Execute adapter with input."""
        return await self.adapter.generate(
            input_data=input,
            model=self.model,
            **self.kwargs,
        )
