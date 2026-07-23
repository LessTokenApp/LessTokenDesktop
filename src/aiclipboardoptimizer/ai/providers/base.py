"""Abstract base classes and interfaces for LLM providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProviderResponse:
    """Response from an LLM provider with token and cost information."""

    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output)."""
        return self.input_tokens + self.output_tokens


class BaseProvider(ABC):
    """Abstract base class for LLM providers (OpenAI, Claude, Gemini, Ollama)."""

    @abstractmethod
    def process(self, prompt: str, model: str) -> ProviderResponse:
        """
        Execute a prompt and return response with token counts and cost.

        Args:
            prompt: The prompt text to send to the model
            model: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")

        Returns:
            ProviderResponse with text, token counts, and cost

        Raises:
            ValueError: If model is not supported or credentials missing
            RuntimeError: If API call fails
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text without making an API call (when possible).

        Args:
            text: Text to tokenize
            model: Model identifier for accurate token counting

        Returns:
            Number of tokens

        Note:
            Some providers require API calls for accurate counting.
            Implementations may return estimates when necessary.
        """
        pass

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for a prompt based on token counts.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model identifier

        Returns:
            Estimated cost in USD

        Override this method if pricing is model-dependent.
        """
        raise NotImplementedError("Subclass must implement cost estimation")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g., 'OpenAI', 'Claude', 'Gemini')."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of model identifiers supported by this provider."""
        pass
