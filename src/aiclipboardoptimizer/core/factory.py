"""Provider factory for creating LLM provider instances."""
from typing import TYPE_CHECKING, Optional, Type
from .logger import Logger

if TYPE_CHECKING:
    from ..ai.providers.base import BaseProvider

logger = Logger.get(__name__)


class ProviderFactory:
    """Factory for creating LLM provider instances based on config."""

    _providers: dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type) -> None:
        """Register a provider class.

        Args:
            name: Provider name (e.g., 'openai', 'claude')
            provider_class: Provider class implementing BaseProvider
        """
        cls._providers[name.lower()] = provider_class
        logger.debug(f"Registered provider: {name}")

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> "BaseProvider":
        """Create provider instance.

        Args:
            provider_name: Name of provider to create
            **kwargs: Arguments passed to provider constructor

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not registered
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not registered. "
                f"Available: {available}"
            )

        provider_class = cls._providers[provider_name]
        logger.info(f"Creating provider instance: {provider_name}")
        return provider_class(**kwargs)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if provider is registered."""
        return name.lower() in cls._providers
