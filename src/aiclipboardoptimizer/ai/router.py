"""Model selection router for cost optimization."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelRecommendation:
    """Model selection recommendation."""

    provider: str
    model: str
    reason: str
    estimated_monthly_savings: float  # If switching from current model


class ModelRouter:
    """Route to optimal model based on task complexity and budget preference."""

    # Model capabilities and costs (relative to each other)
    CLAUDE_MODELS = {
        "claude-3-5-haiku-20241022": {
            "tier": "budget",
            "speed": "fast",
            "cost_relative": 1.0,  # Baseline
            "quality": 3,  # 1-5 scale
            "supports_images": True,
        },
        "claude-3-5-sonnet-20241022": {
            "tier": "standard",
            "speed": "medium",
            "cost_relative": 5.0,
            "quality": 4,
            "supports_images": True,
        },
        "claude-3-opus-20250219": {
            "tier": "premium",
            "speed": "slow",
            "cost_relative": 15.0,
            "quality": 5,
            "supports_images": True,
        },
    }

    OPENAI_MODELS = {
        "gpt-4o-mini": {
            "tier": "budget",
            "speed": "fast",
            "cost_relative": 1.5,
            "quality": 3,
            "supports_images": True,
        },
        "gpt-4o": {
            "tier": "standard",
            "speed": "medium",
            "cost_relative": 8.0,
            "quality": 4,
            "supports_images": True,
        },
        "gpt-4-turbo": {
            "tier": "premium",
            "speed": "slow",
            "cost_relative": 20.0,
            "quality": 5,
            "supports_images": True,
        },
    }

    GEMINI_MODELS = {
        "gemini-2.5-flash": {
            "tier": "budget",
            "speed": "fast",
            "cost_relative": 0.8,
            "quality": 3,
            "supports_images": True,
        },
        "gemini-2.0-flash": {
            "tier": "standard",
            "speed": "medium",
            "cost_relative": 1.0,
            "quality": 3.5,
            "supports_images": True,
        },
        "gemini-1.5-pro": {
            "tier": "premium",
            "speed": "slow",
            "cost_relative": 10.0,
            "quality": 4,
            "supports_images": True,
        },
    }

    # Operation complexity levels
    OPERATION_COMPLEXITY = {
        "clean": 1,  # Simple
        "shorten": 1,
        "formal": 2,  # Medium
        "email": 2,
        "summarize": 2,
        "bullets": 1,
        "translate_en": 3,  # Complex
    }

    def __init__(self, default_provider: str = "claude", quality_level: str = "balanced") -> None:
        """Initialize router."""
        self.default_provider = default_provider.lower()
        self.quality_level = quality_level.lower()

        if self.quality_level not in ("budget", "balanced", "premium"):
            self.quality_level = "balanced"

    def recommend_model(
        self,
        text_length: int,
        operation: str = "clean",
        provider: Optional[str] = None,
    ) -> ModelRecommendation:
        """
        Recommend optimal model for a task.

        Args:
            text_length: Length of input text in characters
            operation: Operation type (clean, summarize, etc.)
            provider: Force specific provider (None = use default)

        Returns:
            ModelRecommendation with selected model and reasoning
        """
        if provider is None:
            provider = self.default_provider

        provider = provider.lower()
        complexity = self.OPERATION_COMPLEXITY.get(operation, 2)

        # Estimate tokens (rough: 4 chars per token)
        estimated_tokens = max(1, text_length // 4)

        if provider == "claude":
            return self._recommend_claude(estimated_tokens, complexity)
        elif provider == "openai":
            return self._recommend_openai(estimated_tokens, complexity)
        elif provider == "gemini":
            return self._recommend_gemini(estimated_tokens, complexity)
        elif provider == "ollama":
            # Ollama is always free, use best available
            return ModelRecommendation(
                provider="ollama",
                model="mistral",
                reason="Local Ollama model (free)",
                estimated_monthly_savings=0,
            )
        else:
            # Fallback to Claude
            return self._recommend_claude(estimated_tokens, complexity)

    def _recommend_claude(self, estimated_tokens: int, complexity: int) -> ModelRecommendation:
        """Recommend Claude model based on complexity and budget."""
        if self.quality_level == "budget":
            # Always use cheapest
            return ModelRecommendation(
                provider="claude",
                model="claude-3-5-haiku-20241022",
                reason=f"Budget mode: Haiku (90% cheaper for tasks <500 tokens)",
                estimated_monthly_savings=0,
            )

        elif self.quality_level == "premium":
            # Always use best
            return ModelRecommendation(
                provider="claude",
                model="claude-3-opus-20250219",
                reason="Premium mode: Best quality regardless of cost",
                estimated_monthly_savings=0,
            )

        else:  # balanced
            # Choose based on complexity
            if complexity <= 1 and estimated_tokens < 100:
                return ModelRecommendation(
                    provider="claude",
                    model="claude-3-5-haiku-20241022",
                    reason=f"Simple task (<100 tokens): Using Haiku (90% cost savings)",
                    estimated_monthly_savings=0,
                )
            elif complexity <= 2 and estimated_tokens < 500:
                return ModelRecommendation(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    reason=f"Medium task (<500 tokens): Using Sonnet (40% cost savings)",
                    estimated_monthly_savings=0,
                )
            else:
                return ModelRecommendation(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    reason=f"Complex task or long text: Using Sonnet (balanced)",
                    estimated_monthly_savings=0,
                )

    def _recommend_openai(self, estimated_tokens: int, complexity: int) -> ModelRecommendation:
        """Recommend OpenAI model based on complexity and budget."""
        if self.quality_level == "budget":
            return ModelRecommendation(
                provider="openai",
                model="gpt-4o-mini",
                reason="Budget mode: Using cheapest GPT-4o mini",
                estimated_monthly_savings=0,
            )

        elif self.quality_level == "premium":
            return ModelRecommendation(
                provider="openai",
                model="gpt-4-turbo",
                reason="Premium mode: Using GPT-4 Turbo for best quality",
                estimated_monthly_savings=0,
            )

        else:  # balanced
            if complexity <= 1 and estimated_tokens < 100:
                return ModelRecommendation(
                    provider="openai",
                    model="gpt-4o-mini",
                    reason="Simple task: Using GPT-4o mini (80% cheaper)",
                    estimated_monthly_savings=0,
                )
            else:
                return ModelRecommendation(
                    provider="openai",
                    model="gpt-4o",
                    reason="Medium/complex task: Using GPT-4o (balanced)",
                    estimated_monthly_savings=0,
                )

    def _recommend_gemini(self, estimated_tokens: int, complexity: int) -> ModelRecommendation:
        """Recommend Gemini model based on complexity and budget."""
        if self.quality_level == "budget":
            return ModelRecommendation(
                provider="gemini",
                model="gemini-2.5-flash",
                reason="Budget mode: Using Gemini Flash (cheapest)",
                estimated_monthly_savings=0,
            )

        elif self.quality_level == "premium":
            return ModelRecommendation(
                provider="gemini",
                model="gemini-1.5-pro",
                reason="Premium mode: Using Gemini 1.5 Pro for best quality",
                estimated_monthly_savings=0,
            )

        else:  # balanced
            if complexity <= 1:
                return ModelRecommendation(
                    provider="gemini",
                    model="gemini-2.5-flash",
                    reason="Simple task: Using Gemini Flash (90% cheaper)",
                    estimated_monthly_savings=0,
                )
            elif complexity <= 2:
                return ModelRecommendation(
                    provider="gemini",
                    model="gemini-2.0-flash",
                    reason="Medium task: Using Gemini 2.0 Flash (balanced)",
                    estimated_monthly_savings=0,
                )
            else:
                return ModelRecommendation(
                    provider="gemini",
                    model="gemini-1.5-pro",
                    reason="Complex task: Using Gemini 1.5 Pro",
                    estimated_monthly_savings=0,
                )

    def get_available_models(self, provider: str) -> dict:
        """Get all available models for a provider."""
        provider = provider.lower()
        if provider == "claude":
            return self.CLAUDE_MODELS
        elif provider == "openai":
            return self.OPENAI_MODELS
        elif provider == "gemini":
            return self.GEMINI_MODELS
        return {}
