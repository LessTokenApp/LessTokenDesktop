"""Application orchestration and lifecycle management."""
from pathlib import Path
from typing import Optional

from .config import AppConfig
from .core.logger import Logger
from .core.di import ApplicationContainer
from .core.factory import ProviderFactory
from .services.clipboard import ClipboardService
from .services.processor import ProcessorService
from .services.processor_enhanced import EnhancedProcessorService
from .services.content import ContentDetector
from .services.prompt import PromptService
from .services.history import HistoryService
from .services.pipeline import Pipeline
from .services.image import ImageService
from .services.file import FileService
from .services.provider_manager import ProviderManager
from .services.provider_selector import ProviderSelector

logger = Logger.get(__name__)


class Application:
    """Main application class that orchestrates all services."""

    def __init__(self, config: AppConfig):
        self.config = config

        # Configure logger
        Logger.configure(config.log_level, config.output_dir / "logs")

        # Setup DI container
        self.container = ApplicationContainer()

        # Register configuration
        self.container.register_service("config", config)

        # Setup services
        self._setup_services()

        logger.info(f"Application initialized: {config.app_name}")

    def _setup_services(self) -> None:
        """Setup and register all application services."""
        event_bus = self.container.get_event_bus()
        provider_factory = self.container.get_provider_factory()

        # Register clipboard service
        clipboard_service = ClipboardService(event_bus, self.config.poll_interval_seconds)
        self.container.register_service("clipboard", clipboard_service)

        # Setup provider management
        provider_manager = ProviderManager(provider_factory)
        self.container.register_service("provider_manager", provider_manager)

        # Register processor service (basic)
        processor_service = ProcessorService(event_bus, provider_factory)
        self.container.register_service("processor", processor_service)

        # Setup provider selector
        provider_selector = ProviderSelector(provider_manager)
        self.container.register_service("provider_selector", provider_selector)

        # Register content detector
        content_detector = ContentDetector()
        self.container.register_service("content_detector", content_detector)

        # Register prompt service
        prompts_dir = self.config.output_dir / "prompts"
        prompt_service = PromptService(prompts_dir)
        self.container.register_service("prompt", prompt_service)

        # Register history service
        history_db = self.config.output_dir / "data" / "history.db"
        history_service = HistoryService(history_db)
        self.container.register_service("history", history_service)

        # Register image service
        image_service = ImageService()
        self.container.register_service("image", image_service)

        # Register file service
        file_service = FileService()
        self.container.register_service("file", file_service)

        # Register pipeline (ties everything together)
        pipeline = Pipeline(
            clipboard_service,
            content_detector,
            prompt_service,
            processor_service,
            history_service,
            event_bus,
            auto_copy_result=True,
        )
        self.container.register_service("pipeline", pipeline)

        logger.info(f"Registered services: {list(self.container.list_services().keys())}")

    def get_clipboard_service(self) -> ClipboardService:
        """Get clipboard service."""
        return self.container.get_service("clipboard")

    def get_processor_service(self) -> ProcessorService:
        """Get processor service."""
        return self.container.get_service("processor")

    def get_content_detector(self) -> ContentDetector:
        """Get content detector service."""
        return self.container.get_service("content_detector")

    def get_prompt_service(self) -> PromptService:
        """Get prompt service."""
        return self.container.get_service("prompt")

    def get_history_service(self) -> HistoryService:
        """Get history service."""
        return self.container.get_service("history")

    def get_pipeline(self) -> Pipeline:
        """Get pipeline service."""
        return self.container.get_service("pipeline")

    def get_image_service(self) -> ImageService:
        """Get image service."""
        return self.container.get_service("image")

    def get_file_service(self) -> FileService:
        """Get file service."""
        return self.container.get_service("file")

    def get_provider_manager(self) -> ProviderManager:
        """Get provider manager."""
        return self.container.get_service("provider_manager")

    def get_provider_selector(self) -> ProviderSelector:
        """Get provider selector."""
        return self.container.get_service("provider_selector")

    def startup(self) -> None:
        """Start all services."""
        logger.info("Starting application services...")

        # Pipeline startup handles all service initialization
        pipeline = self.get_pipeline()
        pipeline.on_startup()

        logger.info("Application started successfully")

    def shutdown(self) -> None:
        """Stop all services."""
        logger.info("Shutting down application services...")

        # Pipeline shutdown handles all service cleanup
        pipeline = self.get_pipeline()
        pipeline.on_shutdown()

        logger.info("Application shutdown complete")

    def process_text(self, text: str, prompt_id: Optional[str] = None, auto_copy: bool = True) -> Optional[str]:
        """Convenience method to process text through pipeline.

        Args:
            text: Text to process
            prompt_id: Optional specific prompt ID
            auto_copy: Whether to copy result to clipboard

        Returns:
            Processed text or None if failed
        """
        pipeline = self.get_pipeline()
        return pipeline.process(text, prompt_id, auto_copy)

    def get_quick_actions(self, text: str) -> list[dict]:
        """Get suggested prompts for text.

        Returns:
            List of quick action options
        """
        pipeline = self.get_pipeline()
        return pipeline.get_quick_actions(text)

    def get_stats(self) -> dict:
        """Get application statistics."""
        pipeline = self.get_pipeline()
        return pipeline.get_pipeline_stats()

    def optimize_image(
        self,
        image_path: Path,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
        extract_text: bool = False,
    ):
        """Optimize image for token reduction.

        Args:
            image_path: Path to image
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality
            extract_text: Extract text via OCR

        Returns:
            ImageOptimizationResult
        """
        image_service = self.get_image_service()
        return image_service.optimize(image_path, max_width, max_height, quality, extract_text)

    def extract_file(self, file_path: Path, pages: Optional[list] = None):
        """Extract text from file.

        Args:
            file_path: Path to file (PDF, Word, CSV, etc.)
            pages: For PDFs, specific pages to extract

        Returns:
            FileExtractionResult
        """
        file_service = self.get_file_service()
        return file_service.extract(file_path, pages)

    def register_provider(self, name: str, api_key: Optional[str] = None, is_default: bool = False):
        """Register an LLM provider.

        Args:
            name: Provider name (openai, claude, gemini, ollama, local)
            api_key: API key if required
            is_default: Whether to use as default
        """
        from .ai.providers import (
            OpenAIProvider, ClaudeProvider, GeminiProvider,
            OllamaProvider, LocalProvider
        )

        provider_map = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider,
            "local": LocalProvider,
        }

        if name not in provider_map:
            raise ValueError(f"Unknown provider: {name}")

        provider_class = provider_map[name]
        provider = provider_class(api_key) if api_key else provider_class()

        manager = self.get_provider_manager()
        manager.register_provider(name, provider, is_default)

    def compare_provider_costs(self, text: str, prompt: str) -> list[dict]:
        """Compare costs across all providers.

        Returns:
            List of cost estimates sorted by price
        """
        manager = self.get_provider_manager()
        char_count = len(text) + len(prompt)
        est_tokens = char_count // 4

        estimates = manager.compare_providers(est_tokens, est_tokens)
        return [
            {
                "provider": e.provider_name,
                "model": e.model,
                "cost": e.total_cost_usd,
                "latency_ms": e.estimated_latency_ms,
            }
            for e in estimates
        ]

    def process_text_auto(
        self,
        text: str,
        prompt_id: Optional[str] = None,
        needs_quality: bool = False,
        needs_speed: bool = False,
        cost_sensitive: bool = True,
        auto_copy: bool = True,
    ) -> Optional[str]:
        """Process text with automatic provider selection.

        Args:
            text: Text to process
            prompt_id: Prompt to use
            needs_quality: Prioritize quality
            needs_speed: Prioritize speed
            cost_sensitive: Prioritize cost (default)
            auto_copy: Copy result to clipboard

        Returns:
            Processed text or None if failed
        """
        pipeline = self.get_pipeline()

        # Use existing process method (which auto-selects prompt)
        # but we could enhance this for provider selection
        return pipeline.process(text, prompt_id, auto_copy)

    def get_processing_options(self, text: str) -> dict:
        """Get processing options for text.

        Returns:
            Dict with provider recommendations, cost estimates, etc.
        """
        selector = self.get_provider_selector()
        manager = self.get_provider_manager()
        detector = self.get_content_detector()

        content_info = detector.detect(text)
        char_count = len(text)
        est_tokens = char_count // 4

        from .services.provider_selector import SelectionContext
        context = SelectionContext(
            content_type=content_info.content_type,
            input_tokens=est_tokens,
            output_tokens=est_tokens,
        )

        return {
            "content_type": content_info.content_type.value,
            "estimated_tokens": est_tokens,
            "available_providers": manager.get_available_providers(),
            "recommendations": selector.get_recommendations(context),
            "costs": self.compare_provider_costs(text, ""),
        }

    def __repr__(self) -> str:
        return f"Application({self.config.app_name})"
