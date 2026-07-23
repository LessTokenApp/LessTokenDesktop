"""Dependency Injection container for the application."""
from typing import Any, Callable, Optional, TypeVar
from dataclasses import dataclass, field

from .logger import Logger
from .events import EventBus
from .factory import ProviderFactory

logger = Logger.get(__name__)

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._instances_by_type: dict[type, Any] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance.

        Args:
            name: Service name
            instance: Singleton instance
        """
        self._singletons[name] = instance
        self._instances_by_type[type(instance)] = instance
        logger.debug(f"Registered singleton: {name}")

    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """Register a factory function.

        Args:
            name: Service name
            factory: Callable that creates instances
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")

    def get(self, name: str, *args, **kwargs) -> Any:
        """Get instance by name.

        Args:
            name: Service name
            *args, **kwargs: Arguments for factory if applicable

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]

        # Then factories
        if name in self._factories:
            return self._factories[name](*args, **kwargs)

        raise KeyError(f"Service '{name}' not registered in DI container")

    def get_by_type(self, service_type: type[T]) -> T:
        """Get instance by type.

        Args:
            service_type: Type of service

        Returns:
            Service instance

        Raises:
            KeyError: If service type not found
        """
        if service_type in self._instances_by_type:
            return self._instances_by_type[service_type]

        raise KeyError(f"Service of type '{service_type.__name__}' not registered")

    def list_services(self) -> dict[str, str]:
        """List all registered services."""
        return {
            **{name: "singleton" for name in self._singletons},
            **{name: "factory" for name in self._factories},
        }


class ApplicationContainer:
    """Application-level DI container with standard services."""

    def __init__(self) -> None:
        self.di = DIContainer()
        self._setup_core_services()

    def _setup_core_services(self) -> None:
        """Set up core application services."""
        # Register EventBus singleton
        event_bus = EventBus()
        self.di.register_singleton("event_bus", event_bus)

        # Register ProviderFactory singleton
        provider_factory = ProviderFactory()
        self.di.register_singleton("provider_factory", provider_factory)

    def get_event_bus(self) -> EventBus:
        """Get EventBus singleton."""
        return self.di.get("event_bus")

    def get_provider_factory(self) -> ProviderFactory:
        """Get ProviderFactory singleton."""
        return self.di.get("provider_factory")

    def register_service(self, name: str, instance: Any) -> None:
        """Register a service instance."""
        self.di.register_singleton(name, instance)

    def get_service(self, name: str) -> Any:
        """Get registered service by name."""
        return self.di.get(name)

    def list_services(self) -> dict[str, str]:
        """List all registered services."""
        return self.di.list_services()
