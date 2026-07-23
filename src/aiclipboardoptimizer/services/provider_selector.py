"""Intelligent provider selection based on content and requirements."""
from dataclasses import dataclass
from typing import Optional

from .base import BaseService
from .content import ContentType
from .provider_manager import ProviderManager, SelectionCriteria
from ..core.logger import Logger

logger = Logger.get(__name__)


@dataclass
class SelectionContext:
    """Context for provider selection."""
    content_type: ContentType
    input_tokens: int
    output_tokens: int
    needs_quality: bool = False
    needs_speed: bool = False
    cost_sensitive: bool = True
    requires_local: bool = False


class ProviderSelector(BaseService):
    """Intelligently select providers based on content and requirements."""

    # Provider suitability for content types
    CONTENT_PREFERENCES = {
        ContentType.CODE: {
            "best": ["gpt-4o", "claude"],  # Strong code reasoning
            "fallback": ["gemini"],
        },
        ContentType.TEXT: {
            "best": ["claude", "gpt-4o"],  # Strong text skills
            "fallback": ["gemini", "ollama"],
        },
        ContentType.EMAIL: {
            "best": ["claude", "gpt-4o-mini"],  # Good for writing
            "fallback": ["gemini", "ollama"],
        },
        ContentType.MARKDOWN: {
            "best": ["claude", "gpt-4o"],
            "fallback": ["gemini"],
        },
        ContentType.JSON: {
            "best": ["gpt-4o", "claude"],  # Strong structure understanding
            "fallback": ["gemini"],
        },
        ContentType.YAML: {
            "best": ["gpt-4o", "claude"],
            "fallback": ["gemini", "ollama"],
        },
    }

    # Token budget thresholds for provider selection
    TOKEN_BUDGETS = {
        "ultra_cheap": 1000,        # Prefer cheapest (local, ollama)
        "cheap": 5000,              # Prefer cheap (gpt-4o-mini)
        "moderate": 20000,          # More flexibility
        "generous": 100000,         # Use best provider
    }

    # Latency budget (ms)
    LATENCY_BUDGETS = {
        "instant": 200,
        "quick": 500,
        "normal": 1000,
        "patient": 2000,
    }

    def __init__(self, provider_manager: ProviderManager):
        self.manager = provider_manager

    @property
    def service_name(self) -> str:
        return "provider_selector"

    def select(self, context: SelectionContext) -> tuple[Optional[str], Optional[str]]:
        """Select best provider for given context.

        Args:
            context: SelectionContext with requirements

        Returns:
            (provider_name, model_name) tuple
        """
        logger.debug(
            f"Selecting provider: {context.content_type}, "
            f"{context.input_tokens} tokens, "
            f"quality={context.needs_quality}, speed={context.needs_speed}"
        )

        # 1. Check if local-only requirement
        if context.requires_local:
            return self._select_local(context)

        # 2. Get preferred providers for content type
        preferences = self.CONTENT_PREFERENCES.get(
            context.content_type,
            {"best": [], "fallback": []},
        )

        # 3. Apply selection criteria
        if context.needs_quality:
            return self._select_for_quality(preferences, context)
        elif context.needs_speed:
            return self._select_for_speed(preferences, context)
        elif context.cost_sensitive:
            return self._select_for_cost(preferences, context)
        else:
            return self._select_balanced(preferences, context)

    def _select_local(self, context: SelectionContext) -> tuple[Optional[str], Optional[str]]:
        """Select local provider only."""
        provider_name, model = self.manager.select_best_provider(
            SelectionCriteria.LOCAL
        )
        logger.info(f"Selected local provider: {provider_name}/{model}")
        return provider_name, model

    def _select_for_quality(
        self,
        preferences: dict,
        context: SelectionContext,
    ) -> tuple[Optional[str], Optional[str]]:
        """Select best quality provider."""
        available = self.manager.get_available_providers()

        # Try preferred providers first
        for preferred in preferences["best"]:
            if preferred in available:
                info = self.manager.get_provider_info(preferred)
                logger.info(f"Selected for quality: {preferred}/{info.default_model}")
                return preferred, info.default_model

        # Fallback
        for fallback in preferences["fallback"]:
            if fallback in available:
                info = self.manager.get_provider_info(fallback)
                logger.info(f"Selected (fallback): {fallback}/{info.default_model}")
                return fallback, info.default_model

        # Last resort
        provider_name, model = self.manager.select_best_provider(SelectionCriteria.QUALITY)
        return provider_name, model

    def _select_for_speed(
        self,
        preferences: dict,
        context: SelectionContext,
    ) -> tuple[Optional[str], Optional[str]]:
        """Select fastest provider."""
        available = self.manager.get_available_providers()

        # Prefer local for speed
        if "local" in available:
            info = self.manager.get_provider_info("local")
            logger.info(f"Selected for speed: local/{info.default_model}")
            return "local", info.default_model

        if "ollama" in available:
            info = self.manager.get_provider_info("ollama")
            logger.info(f"Selected for speed: ollama/{info.default_model}")
            return "ollama", info.default_model

        # Otherwise use speed selection
        provider_name, model = self.manager.select_best_provider(SelectionCriteria.FASTEST)
        return provider_name, model

    def _select_for_cost(
        self,
        preferences: dict,
        context: SelectionContext,
    ) -> tuple[Optional[str], Optional[str]]:
        """Select cheapest provider."""
        available = self.manager.get_available_providers()

        # Determine cost sensitivity
        total_tokens = context.input_tokens + context.output_tokens

        if total_tokens < self.TOKEN_BUDGETS["ultra_cheap"]:
            # Very cheap - prefer local
            if "local" in available:
                info = self.manager.get_provider_info("local")
                logger.info(f"Selected (ultra-cheap): local/{info.default_model}")
                return "local", info.default_model

            if "ollama" in available:
                info = self.manager.get_provider_info("ollama")
                logger.info(f"Selected (ultra-cheap): ollama/{info.default_model}")
                return "ollama", info.default_model

        # For moderate tokens, use cost comparison
        estimates = self.manager.compare_providers(
            context.input_tokens,
            context.output_tokens,
        )

        if estimates:
            chosen = estimates[0]
            logger.info(
                f"Selected for cost: {chosen.provider_name}/"
                f"{chosen.model} (${chosen.total_cost_usd:.6f})"
            )
            return chosen.provider_name, chosen.model

        # Fallback to cheapest
        provider_name, model = self.manager.select_best_provider(SelectionCriteria.CHEAPEST)
        return provider_name, model

    def _select_balanced(
        self,
        preferences: dict,
        context: SelectionContext,
    ) -> tuple[Optional[str], Optional[str]]:
        """Select balanced provider (cost + quality + speed)."""
        available = self.manager.get_available_providers()

        # Check if content preference available
        for preferred in preferences["best"]:
            if preferred in available:
                estimates = self.manager.compare_providers(
                    context.input_tokens,
                    context.output_tokens,
                    {preferred: self.manager.get_provider_info(preferred).default_model},
                )
                if estimates:
                    chosen = estimates[0]
                    logger.info(f"Selected (balanced): {chosen.provider_name}/{chosen.model}")
                    return chosen.provider_name, chosen.model

        # Use balanced selection
        provider_name, model = self.manager.select_best_provider(SelectionCriteria.BALANCED)
        return provider_name, model

    def get_recommendations(self, context: SelectionContext) -> dict:
        """Get provider recommendations for context.

        Returns:
            Dict with recommendations for different criteria
        """
        quality = self._select_for_quality(
            self.CONTENT_PREFERENCES.get(context.content_type, {"best": [], "fallback": []}),
            context,
        )
        speed = self._select_for_speed(
            self.CONTENT_PREFERENCES.get(context.content_type, {"best": [], "fallback": []}),
            context,
        )
        cost = self._select_for_cost(
            self.CONTENT_PREFERENCES.get(context.content_type, {"best": [], "fallback": []}),
            context,
        )
        balanced = self._select_balanced(
            self.CONTENT_PREFERENCES.get(context.content_type, {"best": [], "fallback": []}),
            context,
        )

        return {
            "quality": quality,
            "speed": speed,
            "cost": cost,
            "balanced": balanced,
        }

    def on_startup(self) -> None:
        """Initialize provider selector."""
        logger.info("Provider selector started")

    def on_shutdown(self) -> None:
        """Shutdown provider selector."""
        logger.info("Provider selector stopped")
