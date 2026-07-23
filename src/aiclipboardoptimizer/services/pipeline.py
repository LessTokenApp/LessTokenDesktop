"""Pipeline service orchestrating the complete clipboard processing flow."""
import threading
from typing import Optional, Callable
from datetime import datetime

from .base import BaseService
from .clipboard import ClipboardService
from .content import ContentDetector, ContentInfo
from .prompt import PromptService
from .processor import ProcessorService
from .history import HistoryService
from ..core.logger import Logger
from ..core.events import EventBus, ClipboardChangedEvent

logger = Logger.get(__name__)


class Pipeline(BaseService):
    """
    Complete pipeline: Monitor → Detect → Prompt → AI → Format → History

    Flow:
    1. Monitor clipboard for changes
    2. Detect content type
    3. Find matching prompts
    4. Execute AI processing
    5. Save to history
    6. Copy result to clipboard (optional)
    """

    def __init__(
        self,
        clipboard_service: ClipboardService,
        content_detector: ContentDetector,
        prompt_service: PromptService,
        processor_service: ProcessorService,
        history_service: HistoryService,
        event_bus: EventBus,
        auto_copy_result: bool = True,
    ):
        self.clipboard = clipboard_service
        self.detector = content_detector
        self.prompts = prompt_service
        self.processor = processor_service
        self.history = history_service
        self.event_bus = event_bus
        self.auto_copy_result = auto_copy_result

        self._is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_processed: Optional[str] = None

        # Subscribe to clipboard changes
        self.event_bus.subscribe("clipboard:changed", self._on_clipboard_changed)

    @property
    def service_name(self) -> str:
        return "pipeline"

    def start_monitoring(self) -> None:
        """Start clipboard monitoring in background thread."""
        if self._is_running:
            logger.warning("Pipeline already running")
            return

        self._is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Pipeline monitoring started")

    def stop_monitoring(self) -> None:
        """Stop clipboard monitoring."""
        self._is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

        logger.info("Pipeline monitoring stopped")

    def process(
        self,
        content: str,
        prompt_id: Optional[str] = None,
        auto_copy: Optional[bool] = None,
    ) -> Optional[str]:
        """Process content through pipeline.

        Args:
            content: Content to process
            prompt_id: Optional specific prompt to use
            auto_copy: Override auto_copy_result setting

        Returns:
            Processed content, or None if processing failed
        """
        logger.debug(f"Processing {len(content)} chars: {content[:50]}...")

        try:
            # Step 1: Detect content type
            content_info = self.detector.detect(content)
            logger.debug(f"Detected content type: {content_info.content_type}")

            # Step 2: Select prompt
            if not prompt_id:
                # Auto-select based on content type
                suitable_prompts = self.prompts.get_prompts_for_content_type(
                    content_info.content_type
                )

                if not suitable_prompts:
                    logger.warning(f"No prompts for {content_info.content_type}")
                    return None

                prompt = suitable_prompts[0]  # Use first suitable prompt
            else:
                prompt = self.prompts.get_prompt(prompt_id)
                if not prompt:
                    logger.error(f"Prompt not found: {prompt_id}")
                    return None

            logger.debug(f"Using prompt: {prompt.name}")

            # Step 3: Format prompt with content
            formatted_prompt = prompt.content.format(text=content) if "{text}" in prompt.content else prompt.content

            # Step 4: Process through AI
            result = self.processor.process(content, formatted_prompt)

            if not result.success:
                logger.error(f"Processing failed: {result.error}")
                return None

            processed_content = result.processed_text

            # Step 5: Save to history
            self.history.add_entry(
                original_content=content,
                processed_content=processed_content,
                content_type=content_info.content_type,
                prompt_id=prompt.id,
                prompt_name=prompt.name,
                provider=result.provider_name,
                model=result.model_used,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
                metadata={
                    "language": content_info.language,
                    "confidence": content_info.confidence,
                },
            )

            # Increment prompt usage
            self.prompts.increment_usage(prompt.id)

            logger.info(
                f"Processing complete: {result.input_tokens} → {result.output_tokens} tokens, "
                f"${result.cost_usd:.6f}"
            )

            # Step 6: Copy to clipboard if enabled
            if auto_copy or (auto_copy is None and self.auto_copy_result):
                self.clipboard.write_text(processed_content) if hasattr(self.clipboard, 'write_text') else None
                logger.debug("Result copied to clipboard")

            return processed_content

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return None

    def process_with_prompt(
        self,
        content: str,
        prompt_id: str,
        auto_copy: bool = True,
    ) -> Optional[str]:
        """Process content with specific prompt."""
        return self.process(content, prompt_id, auto_copy)

    def get_quick_actions(self, content: str) -> list[dict]:
        """Get suggested prompts for content.

        Returns:
            List of {"prompt_id", "prompt_name", "category"} dicts
        """
        content_info = self.detector.detect(content)
        suitable_prompts = self.prompts.get_prompts_for_content_type(content_info.content_type)

        return [
            {
                "prompt_id": p.id,
                "prompt_name": p.name,
                "category": p.category,
            }
            for p in suitable_prompts[:5]  # Limit to 5 suggestions
        ]

    def _monitor_loop(self) -> None:
        """Background monitor loop."""
        try:
            while self._is_running:
                current_content = self.clipboard.read_current() if hasattr(self.clipboard, 'read_current') else None

                if current_content and current_content != self._last_processed:
                    self._last_processed = current_content
                    # Don't auto-process by default, just monitor
                    # Users trigger processing via UI or hotkeys

                import time
                time.sleep(1.0)

        except Exception as e:
            logger.error(f"Monitor loop error: {e}", exc_info=True)

    def _on_clipboard_changed(self, event: ClipboardChangedEvent) -> None:
        """Handle clipboard change event."""
        logger.debug(f"Clipboard changed: {event.content_type}")

    def get_pipeline_stats(self) -> dict:
        """Get pipeline statistics."""
        history_stats = self.history.get_statistics()
        processor_stats = self.processor.get_stats()

        return {
            **history_stats,
            "processor": processor_stats,
            "is_running": self._is_running,
        }

    def on_startup(self) -> None:
        """Start pipeline services."""
        self.clipboard.on_startup()
        self.prompts.on_startup()
        self.processor.on_startup()
        self.history.on_startup()

        self.start_monitoring()
        logger.info("Pipeline started")

    def on_shutdown(self) -> None:
        """Shutdown pipeline services."""
        self.stop_monitoring()

        self.history.on_shutdown()
        self.processor.on_shutdown()
        self.prompts.on_shutdown()
        self.clipboard.on_shutdown()

        logger.info("Pipeline stopped")
