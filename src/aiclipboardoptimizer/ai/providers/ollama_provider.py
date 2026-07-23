"""Ollama (local) provider implementation."""
try:
    import ollama
except ImportError:
    raise ImportError("Ollama provider requires 'ollama' package")

from .base import BaseProvider, ProviderResponse


class OllamaProvider(BaseProvider):
    """LLM provider using locally-run Ollama models."""

    # Supported Ollama models (free, local)
    SUPPORTED_MODELS = [
        "mistral",
        "llama2",
        "neural-chat",
        "starling-lm",
        "openhermes",
        "orca-mini",
    ]

    def process(self, prompt: str, model: str) -> ProviderResponse:
        """Execute prompt via Ollama and return response with token counts."""
        if model not in self.supported_models:
            raise ValueError(f"Model {model} not installed. Available: {self.supported_models}")

        try:
            response = ollama.generate(model=model, prompt=prompt, stream=False)
            input_tokens = self.count_tokens(prompt, model)
            # Estimate output tokens from response
            output_tokens = max(1, len(response["response"].split()) // 2)

            return ProviderResponse(
                text=response["response"],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                cost_usd=0.0,  # Ollama is free (local)
            )
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}") from e

    def count_tokens(self, text: str, model: str) -> int:
        """Estimate token count (Ollama doesn't provide built-in counting)."""
        # Simple heuristic: ~4 characters per token
        estimated_tokens = max(1, len(text) // 4)
        return estimated_tokens

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "Ollama"

    @property
    def supported_models(self) -> list[str]:
        """List Ollama models we support."""
        return self.SUPPORTED_MODELS
