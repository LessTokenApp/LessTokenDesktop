"""Event-driven architecture: Event Bus for async event handling."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
import asyncio
from collections import defaultdict

from .logger import Logger

logger = Logger.get(__name__)


@dataclass
class Event:
    """Base event class for all domain events."""

    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Event({self.event_type}, {self.timestamp.isoformat()})"


class EventBus:
    """Publish-subscribe event bus for decoupled event handling."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._event_history: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe handler to event type.

        Args:
            event_type: Type of event to listen for
            handler: Callable that takes Event
        """
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe handler from event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from {event_type}")

    def publish(self, event: Event) -> None:
        """Publish event to all subscribers.

        Args:
            event: Event to publish
        """
        self._event_history.append(event)
        handlers = self._subscribers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type}")
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)

    def get_event_history(self, event_type: Optional[str] = None) -> list[Event]:
        """Get event history, optionally filtered by type.

        Args:
            event_type: Optional filter by event type

        Returns:
            List of events
        """
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Common application events
@dataclass
class ClipboardChangedEvent(Event):
    """Emitted when clipboard content changes."""
    event_type: str = "clipboard:changed"
    content: str = ""
    content_type: str = "text"  # text, image, file


@dataclass
class ProcessingStartedEvent(Event):
    """Emitted when processing starts."""
    event_type: str = "processing:started"
    prompt_id: str = ""


@dataclass
class ProcessingCompletedEvent(Event):
    """Emitted when processing completes."""
    event_type: str = "processing:completed"
    prompt_id: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0


@dataclass
class HistorySavedEvent(Event):
    """Emitted when history is saved."""
    event_type: str = "history:saved"
    entry_id: str = ""
