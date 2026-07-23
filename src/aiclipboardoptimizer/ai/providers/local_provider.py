"""Local (regex-based) provider implementation - no API calls needed."""
from .base import BaseProvider, ProviderResponse


class LocalProvider(BaseProvider):
    """Offline provider using regex-based text processing (no API calls)."""

    def process(self, prompt: str, model: str) -> ProviderResponse:
        """Process text locally without API calls."""
        # For local provider, we just return empty since actual processing
        # happens in AIProcessor's local fallback path
        return ProviderResponse(
            text="",  # Will be replaced by AIProcessor
            input_tokens=self.count_tokens(prompt, model),
            output_tokens=0,
            model=model,
            cost_usd=0.0,
        )

    def count_tokens(self, text: str, model: str) -> int:
        """Estimate token count (local models use simple heuristic)."""
        # ~4 characters per token (OpenAI average)
        return max(1, len(text) // 4)

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "Local"

    @property
    def supported_models(self) -> list[str]:
        """List local models."""
        return ["regex", "local"]
