"""Claude (Anthropic) provider implementation."""
import base64

from anthropic import Anthropic

from .base import BaseProvider, ProviderResponse


class ClaudeProvider(BaseProvider):
    """LLM provider using Anthropic's Claude models."""

    # Pricing as of Feb 2025 (USD per 1M tokens)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
        "claude-3-opus-20250219": {"input": 15.0, "output": 75.0},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Claude provider with API key."""
        self.client = Anthropic(api_key=api_key)

    def process(self, prompt: str, model: str) -> ProviderResponse:
        """Execute prompt via Claude API and return response with token counts."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_usd = self.estimate_cost(input_tokens, output_tokens, model)

            return ProviderResponse(
                text=response.content[0].text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                cost_usd=cost_usd,
            )
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}") from e

    @property
    def supports_vision(self) -> bool:
        """Claude reads images."""
        return True

    @property
    def default_vision_model(self) -> str:
        """Model used for image reading."""
        return "claude-opus-5"

    def read_image(
        self, image_bytes: bytes, media_type: str, prompt: str, model: str | None = None
    ) -> ProviderResponse:
        """Return the text Claude reads in an image."""
        model = model or self.default_vision_model
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64.b64encode(image_bytes).decode(),
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            # A thinking block can precede the answer, so pick the text block
            # rather than assuming it comes first.
            blocks = [b for b in response.content if getattr(b, "type", None) == "text"]
            if not blocks:
                raise RuntimeError("Claude returned no text block")

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            return ProviderResponse(
                text=blocks[0].text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                cost_usd=self.estimate_cost(input_tokens, output_tokens, model),
            )
        except Exception as e:
            raise RuntimeError(f"Claude image read failed: {e}") from e

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using Claude's count_tokens API."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            response = self.client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except Exception as e:
            raise RuntimeError(f"Token counting failed: {e}") from e

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate cost based on token usage."""
        if model not in self.PRICING:
            # Fallback for unknown models
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "Claude"

    @property
    def supported_models(self) -> list[str]:
        """List Claude models we support."""
        return list(self.PRICING.keys())
