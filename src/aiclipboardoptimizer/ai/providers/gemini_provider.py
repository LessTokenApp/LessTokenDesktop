"""Google Gemini provider implementation."""
try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("Gemini provider requires 'google-generativeai' package")

from .base import BaseProvider, ProviderResponse


class GeminiProvider(BaseProvider):
    """LLM provider using Google's Gemini models."""

    # Pricing as of Feb 2025 (USD per 1M tokens)
    PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Gemini provider with API key."""
        genai.configure(api_key=api_key)
        self.model = None

    def process(self, prompt: str, model: str) -> ProviderResponse:
        """Execute prompt via Gemini API and return response with token counts."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            self.model = genai.GenerativeModel(model)
            response = self.model.generate_content(prompt)

            # Count tokens using the model's count_tokens
            count_result = self.model.count_tokens(prompt)
            input_tokens = count_result.total_tokens

            # Estimate output tokens (rough)
            output_tokens = max(1, len(response.text.split()) // 2)

            cost_usd = self.estimate_cost(input_tokens, output_tokens, model)

            return ProviderResponse(
                text=response.text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                cost_usd=cost_usd,
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}") from e

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using Gemini's token counting API."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            self.model = genai.GenerativeModel(model)
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback estimate
            return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate cost based on token usage."""
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "Gemini"

    @property
    def supported_models(self) -> list[str]:
        """List Gemini models we support."""
        return list(self.PRICING.keys())
