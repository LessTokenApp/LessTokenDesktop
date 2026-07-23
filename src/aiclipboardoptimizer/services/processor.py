"""Text processing service for AI provider coordination."""
from dataclasses import dataclass
from typing import Optional

from .base import BaseService
from ..core.logger import Logger
from ..core.events import EventBus, ProcessingStartedEvent, ProcessingCompletedEvent
from ..core.factory import ProviderFactory
from ..ai.providers.base import BaseProvider, ProviderResponse

logger = Logger.get(__name__)


@dataclass
class ProcessingResult:
    """Result of processing text through AI provider."""

    original_text: str
    processed_text: str
    provider_name: str
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class ProcessorService(BaseService):
    """Service for processing text through AI providers."""

    def __init__(self, event_bus: EventBus, provider_factory: ProviderFactory):
        self.event_bus = event_bus
        self.provider_factory = provider_factory
        self._current_provider: Optional[BaseProvider] = None
        self._total_tokens_used = 0
        self._total_cost = 0.0

    @property
    def service_name(self) -> str:
        return "processor"

    def set_provider(self, provider: BaseProvider) -> None:
        """Set active provider.

        Args:
            provider: Provider instance
        """
        self._current_provider = provider
        logger.info(f"Provider set to: {provider.provider_name}")

    def process(self, text: str, prompt: str, provider_name: Optional[str] = None, model: Optional[str] = None) -> ProcessingResult:
        """Process text with AI provider.

        Args:
            text: Text to process
            prompt: Processing instruction/prompt
            provider_name: Optional provider name override
            model: Optional model override

        Returns:
            ProcessingResult with output and metrics

        Raises:
            ValueError: If no provider configured
            RuntimeError: If processing fails
        """
        if not self._current_provider and not provider_name:
            raise ValueError("No provider configured")

        # Emit start event
        self.event_bus.publish(ProcessingStartedEvent(prompt_id=id(text)))

        try:
            # Use current provider or create one
            provider = self._current_provider
            if provider_name:
                provider = self.provider_factory.create(provider_name)

            # Get model to use
            model_to_use = model or (provider.supported_models[0] if provider.supported_models else "default")

            logger.info(f"Processing with {provider.provider_name}: {model_to_use}")

            # Call provider
            response: ProviderResponse = provider.process(f"{prompt}\n\n{text}", model_to_use)

            # Track metrics
            self._total_tokens_used += response.total_tokens
            self._total_cost += response.cost_usd

            result = ProcessingResult(
                original_text=text,
                processed_text=response.text,
                provider_name=provider.provider_name,
                model_used=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
            )

            # Emit completion event
            self.event_bus.publish(
                ProcessingCompletedEvent(
                    prompt_id=id(text),
                    tokens_used=response.total_tokens,
                    cost_usd=response.cost_usd,
                )
            )

            logger.info(f"Processing completed: {response.total_tokens} tokens, ${response.cost_usd:.6f}")

            return result

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            raise

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "total_tokens_used": self._total_tokens_used,
            "total_cost_usd": self._total_cost,
            "current_provider": self._current_provider.provider_name if self._current_provider else None,
        }

    def on_startup(self) -> None:
        """Start processor service."""
        logger.info("Processor service started")

    def on_shutdown(self) -> None:
        """Shutdown processor service."""
        logger.info(f"Processor service stopped - Total cost: ${self._total_cost:.6f}")
