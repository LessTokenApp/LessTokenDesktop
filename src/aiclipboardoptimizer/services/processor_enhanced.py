"""Enhanced processor service with intelligent provider selection."""
from dataclasses import dataclass
from typing import Optional

from .processor import ProcessorService as BaseProcessorService
from .processor import ProcessingResult
from .provider_manager import ProviderManager
from .provider_selector import ProviderSelector, SelectionContext
from .content import ContentType, ContentDetector
from ..core.logger import Logger
from ..core.events import EventBus

logger = Logger.get(__name__)


@dataclass
class EnhancedProcessingResult(ProcessingResult):
    """Extended processing result with provider info."""
    provider_selected_by: str = "manual"  # manual, cost, speed, quality, balanced
    alternative_providers: dict = None  # Other options with their costs


class EnhancedProcessorService(BaseProcessorService):
    """Enhanced processor with intelligent provider selection."""

    def __init__(
        self,
        event_bus: EventBus,
        provider_manager: ProviderManager,
        provider_selector: ProviderSelector,
        content_detector: Optional[ContentDetector] = None,
    ):
        super().__init__(event_bus, provider_manager)
        self.selector = provider_selector
        self.detector = content_detector
        self.provider_manager = provider_manager

    @property
    def service_name(self) -> str:
        return "processor_enhanced"

    def process_auto(
        self,
        text: str,
        prompt: str,
        content_type: Optional[ContentType] = None,
        needs_quality: bool = False,
        needs_speed: bool = False,
        cost_sensitive: bool = True,
        requires_local: bool = False,
    ) -> Optional[EnhancedProcessingResult]:
        """Process with automatic provider selection.

        Args:
            text: Text to process
            prompt: Processing prompt
            content_type: Optional content type (auto-detect if None)
            needs_quality: Prioritize quality over cost
            needs_speed: Prioritize speed over cost
            cost_sensitive: Prioritize cost (default)
            requires_local: Must use local provider

        Returns:
            EnhancedProcessingResult with provider selection info
        """
        # Auto-detect content type if not provided
        if content_type is None and self.detector:
            info = self.detector.detect(text)
            content_type = info.content_type
        else:
            content_type = content_type or ContentType.TEXT

        # Estimate tokens (rough estimate based on char count)
        # ~1 token per 4 characters
        char_count = len(text) + len(prompt)
        est_tokens = char_count // 4

        logger.debug(f"Auto-selecting provider: {content_type}, ~{est_tokens} tokens")

        # Create selection context
        context = SelectionContext(
            content_type=content_type,
            input_tokens=est_tokens,
            output_tokens=est_tokens,  # Rough estimate
            needs_quality=needs_quality,
            needs_speed=needs_speed,
            cost_sensitive=cost_sensitive,
            requires_local=requires_local,
        )

        # Select provider
        provider_name, model = self.selector.select(context)

        if not provider_name:
            logger.error("No provider available for selection")
            return None

        logger.info(f"Auto-selected provider: {provider_name}/{model}")

        # Get provider instance
        provider = self.provider_manager.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider instance not available: {provider_name}")
            return None

        # Process using selected provider
        self.set_provider(provider)

        try:
            response = provider.process(f"{prompt}\n\n{text}", model)

            # Get recommendations for alternatives
            recommendations = self.selector.get_recommendations(context)
            alternatives = {}

            for criterion, (alt_provider, alt_model) in recommendations.items():
                if alt_provider and alt_provider != provider_name:
                    cost = self.provider_manager.estimate_cost(
                        alt_provider,
                        alt_model,
                        response.input_tokens,
                        response.output_tokens,
                    )
                    alternatives[criterion] = {
                        "provider": alt_provider,
                        "model": alt_model,
                        "estimated_cost": cost,
                    }

            # Track metrics
            self._total_tokens_used += response.total_tokens
            self._total_cost += response.cost_usd

            result = EnhancedProcessingResult(
                original_text=text,
                processed_text=response.text,
                provider_name=provider.provider_name,
                model_used=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
                provider_selected_by="auto",
                alternative_providers=alternatives,
            )

            logger.info(
                f"Processing complete via {provider_name}: "
                f"{response.total_tokens} tokens, "
                f"${response.cost_usd:.6f}"
            )

            return result

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            return None

    def compare_costs(
        self,
        text: str,
        prompt: str,
    ) -> list[dict]:
        """Compare costs across all providers.

        Args:
            text: Text to process
            prompt: Processing prompt

        Returns:
            List of cost estimates sorted by price
        """
        char_count = len(text) + len(prompt)
        est_tokens = char_count // 4

        estimates = self.provider_manager.compare_providers(est_tokens, est_tokens)

        results = []
        for estimate in estimates:
            results.append({
                "provider": estimate.provider_name,
                "model": estimate.model,
                "estimated_cost": estimate.total_cost_usd,
                "latency_ms": estimate.estimated_latency_ms,
                "cost_per_1m_tokens": estimate.total_cost_usd / (est_tokens / 1_000_000)
                if est_tokens > 0 else 0,
            })

        return results

    def get_provider_recommendations(
        self,
        text: str,
        prompt: str,
        content_type: Optional[ContentType] = None,
    ) -> dict:
        """Get provider recommendations for text.

        Returns:
            Dict with recommendations for different criteria
        """
        if content_type is None and self.detector:
            info = self.detector.detect(text)
            content_type = info.content_type
        else:
            content_type = content_type or ContentType.TEXT

        char_count = len(text) + len(prompt)
        est_tokens = char_count // 4

        context = SelectionContext(
            content_type=content_type,
            input_tokens=est_tokens,
            output_tokens=est_tokens,
        )

        return self.selector.get_recommendations(context)

    def on_startup(self) -> None:
        """Initialize enhanced processor."""
        logger.info("Enhanced processor service started")

    def on_shutdown(self) -> None:
        """Shutdown enhanced processor."""
        logger.info(f"Enhanced processor stopped - Total: ${self._total_cost:.6f}")
