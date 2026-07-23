"""Clipboard monitoring and management service."""
from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime

from .base import BaseService
from ..core.logger import Logger
from ..core.events import EventBus, ClipboardChangedEvent

logger = Logger.get(__name__)


@dataclass
class ClipboardEntry:
    """A clipboard history entry."""

    content: str
    content_type: str  # "text", "image", "file"
    timestamp: datetime
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ClipboardService(BaseService):
    """Service for monitoring and managing clipboard content."""

    def __init__(self, event_bus: EventBus, poll_interval: float = 1.0):
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self._history: list[ClipboardEntry] = []
        self._last_content: Optional[str] = None
        self._is_running = False

    @property
    def service_name(self) -> str:
        return "clipboard"

    def get_history(self, limit: int = 100) -> list[ClipboardEntry]:
        """Get recent clipboard history.

        Args:
            limit: Max entries to return

        Returns:
            List of clipboard entries
        """
        return self._history[-limit:]

    def clear_history(self) -> None:
        """Clear clipboard history."""
        self._history.clear()
        logger.info("Clipboard history cleared")

    def add_entry(self, content: str, content_type: str = "text", metadata: dict = None) -> None:
        """Add entry to clipboard history.

        Args:
            content: Content string
            content_type: Type of content
            metadata: Optional metadata dictionary
        """
        entry = ClipboardEntry(
            content=content,
            content_type=content_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self._history.append(entry)
        self.event_bus.publish(
            ClipboardChangedEvent(
                content=content,
                content_type=content_type,
            )
        )
        logger.debug(f"Added clipboard entry: {content_type} ({len(content)} chars)")

    def get_latest(self) -> Optional[ClipboardEntry]:
        """Get latest clipboard entry."""
        return self._history[-1] if self._history else None

    def on_startup(self) -> None:
        """Start clipboard monitoring."""
        self._is_running = True
        logger.info("Clipboard service started")

    def on_shutdown(self) -> None:
        """Stop clipboard monitoring."""
        self._is_running = False
        logger.info("Clipboard service stopped")
