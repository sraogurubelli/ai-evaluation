"""Adapter registry for plugin-based adapter discovery and creation."""

import importlib
import logging
from typing import Any, Callable
from functools import wraps

try:
    from importlib.metadata import entry_points
except ImportError:
    # Python < 3.8 or importlib_metadata not available
    try:
        from importlib_metadata import entry_points
    except ImportError:
        # Fallback if importlib_metadata is not installed
        def entry_points(group=None):
            """Fallback entry_points that returns empty list."""
            return []


from aieval.adapters.base import Adapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry for adapter factories with support for entry points and dynamic registration."""

    def __init__(self):
        """Initialize adapter registry."""
        self._factories: dict[str, Callable[..., Adapter]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._discovered = False

    def register(
        self,
        adapter_type: str,
        factory: Callable[..., Adapter],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register an adapter factory.

        Args:
            adapter_type: Unique identifier for the adapter type
            factory: Factory function that creates adapter instances
            metadata: Optional metadata about the adapter (description, config_keys, etc.)
        """
        if adapter_type in self._factories:
            logger.warning(f"Overriding existing adapter factory: {adapter_type}")

        self._factories[adapter_type] = factory
        if metadata:
            self._metadata[adapter_type] = metadata

        logger.debug(f"Registered adapter factory: {adapter_type}")

    def register_decorator(self, adapter_type: str, metadata: dict[str, Any] | None = None):
        """
        Decorator for registering adapter factories.

        Usage:
            @registry.register_decorator("my_adapter")
            def create_my_adapter(**config):
                return MyAdapter(**config)
        """

        def decorator(factory: Callable[..., Adapter]):
            self.register(adapter_type, factory, metadata)
            return factory

        return decorator

    def register_from_module(
        self,
        adapter_type: str,
        module_path: str,
        class_name: str,
        factory_kwargs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Register an adapter by dynamically importing from a module.

        Args:
            adapter_type: Unique identifier for the adapter type
            module_path: Python module path (e.g., "my_team.adapters")
            class_name: Class name of the adapter
            factory_kwargs: Optional default kwargs to pass to adapter constructor
            metadata: Optional metadata about the adapter
        """
        try:
            module = importlib.import_module(module_path)
            adapter_class = getattr(module, class_name)

            if not issubclass(adapter_class, Adapter):
                raise TypeError(f"{class_name} must be a subclass of Adapter")

            factory_kwargs = factory_kwargs or {}

            def factory(**config):
                """Factory function for dynamically imported adapter."""
                merged_config = {**factory_kwargs, **config}
                return adapter_class(**merged_config)

            self.register(adapter_type, factory, metadata)
            logger.info(
                f"Registered adapter from module: {adapter_type} ({module_path}.{class_name})"
            )

        except ImportError as e:
            raise ValueError(f"Failed to import module {module_path}: {e}") from e
        except AttributeError as e:
            raise ValueError(f"Class {class_name} not found in module {module_path}: {e}") from e

    def discover_entry_points(self, entry_point_group: str = "aieval.adapters") -> None:
        """
        Discover and register adapters from entry points.

        Args:
            entry_point_group: Entry point group name to search for
        """
        if self._discovered:
            return

        try:
            discovered = entry_points(group=entry_point_group)
            for entry_point in discovered:
                try:
                    factory_func = entry_point.load()
                    adapter_type = entry_point.name
                    self.register(adapter_type, factory_func)
                    logger.info(f"Discovered adapter via entry point: {adapter_type}")
                except Exception as e:
                    logger.warning(f"Failed to load entry point {entry_point.name}: {e}")

            self._discovered = True

        except Exception as e:
            logger.warning(f"Failed to discover entry points: {e}")

    def create(self, adapter_type: str, **config: Any) -> Adapter:
        """
        Create an adapter instance using registered factory.

        Args:
            adapter_type: Type of adapter to create
            **config: Configuration to pass to adapter factory

        Returns:
            Adapter instance

        Raises:
            ValueError: If adapter type is not registered
        """
        if adapter_type not in self._factories:
            # Try discovering entry points if not already done
            if not self._discovered:
                self.discover_entry_points()

            if adapter_type not in self._factories:
                available = ", ".join(sorted(self._factories.keys()))
                raise ValueError(
                    f"Unknown adapter type: {adapter_type}. Available types: {available}"
                )

        factory = self._factories[adapter_type]
        try:
            adapter = factory(**config)
            logger.debug(f"Created adapter: {adapter_type}")
            return adapter
        except Exception as e:
            logger.error(f"Failed to create adapter {adapter_type}: {e}")
            raise

    def list_types(self) -> list[dict[str, Any]]:
        """
        List all registered adapter types with metadata.

        Returns:
            List of adapter type metadata dictionaries
        """
        types = []
        for adapter_type, factory in self._factories.items():
            metadata = self._metadata.get(adapter_type, {})
            types.append(
                {
                    "type": adapter_type,
                    "description": metadata.get("description", f"{adapter_type} adapter"),
                    "config_keys": metadata.get("config_keys", []),
                    "factory": factory.__name__ if hasattr(factory, "__name__") else str(factory),
                }
            )
        return types

    def is_registered(self, adapter_type: str) -> bool:
        """Check if an adapter type is registered."""
        return adapter_type in self._factories


# Global registry instance
_default_registry = AdapterRegistry()


def register_adapter(adapter_type: str, metadata: dict[str, Any] | None = None):
    """
    Decorator for registering adapter factories in the default registry.

    Usage:
        @register_adapter("my_adapter", metadata={"description": "My team adapter"})
        def create_my_adapter(**config):
            return MyAdapter(**config)
    """
    return _default_registry.register_decorator(adapter_type, metadata)


def get_registry() -> AdapterRegistry:
    """Get the default adapter registry."""
    return _default_registry
