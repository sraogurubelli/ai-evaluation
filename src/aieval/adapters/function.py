"""Function adapter for Python function-based agents.

This adapter allows you to wrap any Python function (sync or async) as an agent adapter.
Useful for:
- Simple rule-based agents
- Lightweight testing without HTTP server
- Local function evaluation
- Prototype agents during development

Examples:
    Sync function:
        >>> def my_agent(input_data: dict) -> dict:
        ...     return {"output": f"Response to: {input_data.get('prompt', '')}"}
        >>> adapter = FunctionAdapter(fn=my_agent)
        >>> result = await adapter.generate({"prompt": "Hello"})

    Async function:
        >>> async def my_async_agent(input_data: dict) -> dict:
        ...     await asyncio.sleep(0.1)
        ...     return {"output": f"Async response to: {input_data.get('prompt', '')}"}
        >>> adapter = FunctionAdapter(fn=my_async_agent)
        >>> result = await adapter.generate({"prompt": "Hello"})

    With context:
        >>> def agent_with_context(input_data: dict, tenant_id: str) -> dict:
        ...     return {"output": f"[{tenant_id}] Response: {input_data.get('prompt', '')}"}
        >>> adapter = FunctionAdapter(
        ...     fn=agent_with_context,
        ...     context={"tenant_id": "prod"}
        ... )
"""

import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from aieval.adapters.base import Adapter


class FunctionAdapterError(Exception):
    """Base exception for FunctionAdapter errors."""
    pass


class InvalidSignatureError(FunctionAdapterError):
    """Raised when function signature is invalid."""
    pass


class FunctionAdapter(Adapter):
    """
    Adapter that wraps Python functions as agents.
    
    Supports both sync and async functions. Sync functions run in a thread pool
    to avoid blocking the event loop.
    
    Function contract: `agent_fn(input: dict, **kwargs) -> Any`
    - Input: dict with dataset input data
    - Returns: Output (string, dict, or GenerateResult)
    
    Args:
        fn: Python function (sync or async) to wrap
        context: Default context merged with input_data
        validate_signature: Validate function signature at init (default: True)
        executor: ThreadPoolExecutor for sync functions (optional, creates default if None)
    
    Raises:
        InvalidSignatureError: If function signature is invalid and validate_signature=True
    """
    
    def __init__(
        self,
        fn: Callable,
        context: dict[str, Any] | None = None,
        validate_signature: bool = True,
        executor: ThreadPoolExecutor | None = None,
    ):
        """
        Initialize function adapter.
        
        Args:
            fn: Python function (sync or async) to wrap
            context: Default context merged with input_data in all calls
            validate_signature: Validate function signature at init (default: True)
            executor: ThreadPoolExecutor for sync functions (optional)
        
        Raises:
            InvalidSignatureError: If function signature is invalid and validate_signature=True
        """
        if not callable(fn):
            raise InvalidSignatureError(f"fn must be callable, got {type(fn)}")
        
        self.fn = fn
        self.context = context or {}
        self.is_async = inspect.iscoroutinefunction(fn)
        self.executor = executor
        
        # Validate signature if requested
        if validate_signature:
            self._validate_signature()
        
        # Create default executor for sync functions
        if not self.is_async and self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=4, thread_name_prefix="function-adapter"
            )
    
    def _validate_signature(self) -> None:
        """
        Validate function signature.
        
        Ensures function accepts expected parameters.
        
        Raises:
            InvalidSignatureError: If signature is invalid
        """
        sig = inspect.signature(self.fn)
        params = sig.parameters
        
        # Get parameter names (excluding **kwargs)
        param_names = [
            name
            for name, param in params.items()
            if param.kind not in (inspect.Parameter.VAR_KEYWORD,)
        ]
        
        # Function must accept at least one parameter or **kwargs
        if len(param_names) == 0 and not any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        ):
            raise InvalidSignatureError(
                f"Function {self.fn.__name__} must accept at least one parameter or **kwargs"
            )
    
    def _prepare_arguments(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Prepare function arguments from input_data, context, and kwargs.
        
        Merges in order: context -> input_data -> kwargs -> model (if provided)
        
        Args:
            input_data: Input data dict
            model: Model name (optional)
            **kwargs: Additional parameters
        
        Returns:
            Merged arguments dict
        """
        # Merge: context -> input_data -> kwargs -> model
        arguments = {
            **self.context,  # Adapter-level defaults
            **input_data,  # Input data
            **kwargs,  # Additional parameters
        }
        
        if model is not None:
            arguments["model"] = model
        
        return arguments
    
    async def _call_sync(self, arguments: dict[str, Any]) -> Any:
        """
        Call sync function in thread pool.
        
        Args:
            arguments: Function arguments
        
        Returns:
            Function result
        """
        sig = inspect.signature(self.fn)
        params = sig.parameters
        
        # Filter arguments to match function signature
        filtered_args = {}
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        
        for key, value in arguments.items():
            if key in params or has_var_keyword:
                filtered_args[key] = value
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, lambda: self.fn(**filtered_args)
        )
        return result
    
    async def _call_async(self, arguments: dict[str, Any]) -> Any:
        """
        Call async function.
        
        Args:
            arguments: Function arguments
        
        Returns:
            Function result
        """
        sig = inspect.signature(self.fn)
        params = sig.parameters
        
        # Filter arguments to match function signature
        filtered_args = {}
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        
        for key, value in arguments.items():
            if key in params or has_var_keyword:
                filtered_args[key] = value
        
        result = await self.fn(**filtered_args)
        return result
    
    async def generate(
        self,
        input_data: dict[str, Any],
        model: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate output by calling wrapped function.
        
        Args:
            input_data: Input data dict
            model: Model name (optional)
            **kwargs: Additional parameters
        
        Returns:
            Generated output (string, dict, or GenerateResult)
        
        Raises:
            FunctionAdapterError: If function call fails
        """
        # Prepare arguments
        arguments = self._prepare_arguments(input_data, model, **kwargs)
        
        # Call function (sync or async)
        try:
            if self.is_async:
                result = await self._call_async(arguments)
            else:
                result = await self._call_sync(arguments)
        except Exception as e:
            raise FunctionAdapterError(
                f"Function {self.fn.__name__} raised error: {e}"
            ) from e
        
        # Return result as-is (can be string, dict, or GenerateResult)
        return result
    
    def __del__(self):
        """Clean up executor on deletion."""
        if hasattr(self, "executor") and self.executor is not None:
            # Only shutdown if we created the executor
            if not hasattr(self, "_external_executor"):
                self.executor.shutdown(wait=False)
