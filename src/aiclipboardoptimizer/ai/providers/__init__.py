"""LLM provider implementations and factory."""
from .base import BaseProvider, ProviderResponse

__all__ = ["BaseProvider", "ProviderResponse", "ProviderFactory"]


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create(provider: str, api_key: str | None = None) -> BaseProvider:
        """
        Create an LLM provider instance.

        Args:
            provider: Provider name ("claude", "openai", "gemini", "ollama", "local")
            api_key: API key for the provider (optional for local/ollama)

        Returns:
            Configured provider instance

        Raises:
            ValueError: If provider is unknown or required dependencies are missing
        """
        provider = provider.lower().strip()

        if provider == "claude":
            return ClaudeProvider(api_key)
        elif provider == "openai":
            try:
                from .openai_provider import OpenAIProvider
                return OpenAIProvider(api_key)
            except ImportError:
                raise ValueError("OpenAI provider requires 'openai' and 'tiktoken' packages")
        elif provider == "gemini":
            try:
                from .gemini_provider import GeminiProvider
                return GeminiProvider(api_key)
            except ImportError:
                raise ValueError("Gemini provider requires 'google-generativeai' package")
        elif provider == "ollama":
            try:
                from .ollama_provider import OllamaProvider
                return OllamaProvider()
            except ImportError:
                raise ValueError("Ollama provider requires 'ollama' package")
        elif provider == "local":
            from .local_provider import LocalProvider
            return LocalProvider()
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported: claude, openai, gemini, ollama, local"
            )

    @staticmethod
    def list_providers() -> list[str]:
        """List available provider names."""
        return ["claude", "openai", "gemini", "ollama", "local"]
