"""OpenAI provider implementation."""
try:
    import tiktoken
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI provider requires 'openai' and 'tiktoken' packages")

from .base import BaseProvider, ProviderResponse


class OpenAIProvider(BaseProvider):
    """LLM provider using OpenAI's models."""

    # Pricing as of Feb 2025 (USD per 1M tokens)
    PRICING = {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize OpenAI provider with API key."""
        self.client = OpenAI(api_key=api_key)
        self.encoding = None

    @property
    def supports_vision(self) -> bool:
        """GPT-4 class models read images."""
        return True

    @property
    def default_vision_model(self) -> str:
        """Model used for image reading."""
        return "gpt-4.1"

    def read_image(
        self, image_bytes: bytes, media_type: str, prompt: str, model: str | None = None
    ) -> ProviderResponse:
        """Return the text the model reads in an image."""
        import base64

        model = model or self.default_vision_model
        data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode()}"
        try:
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )
            usage = response.usage
            return ProviderResponse(
                text=response.choices[0].message.content or "",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                model=model,
                cost_usd=self.estimate_cost(usage.prompt_tokens, usage.completion_tokens, model),
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI image read failed: {e}") from e

    def process(self, prompt: str, model: str) -> ProviderResponse:
        """Execute prompt via OpenAI API and return response with token counts."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            # Use new messages API (not deprecated responses API)
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost_usd = self.estimate_cost(input_tokens, output_tokens, model)

            return ProviderResponse(
                text=response.choices[0].message.content or "",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                cost_usd=cost_usd,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using tiktoken (client-side, no API call)."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not supported. Available: {self.supported_models}")

        try:
            if self.encoding is None:
                self.encoding = tiktoken.encoding_for_model(model)
            return len(self.encoding.encode(text))
        except Exception as e:
            # Fallback to estimate if tiktoken fails
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
        return "OpenAI"

    @property
    def supported_models(self) -> list[str]:
        """List OpenAI models we support."""
        return list(self.PRICING.keys())
