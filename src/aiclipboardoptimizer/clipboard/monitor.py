"""Clipboard access helpers."""
from collections.abc import Callable
import time

try:
    import pyperclip
except ImportError:  # pragma: no cover - depends on local installation
    pyperclip = None


class ClipboardMonitor:
    """Read and write text from the system clipboard."""

    def __init__(self, poll_interval_seconds: float = 1.0) -> None:
        self.poll_interval_seconds = poll_interval_seconds

    def read_current(self) -> str | None:
        """Return current clipboard text, or None when unavailable."""
        if pyperclip is None:
            return None

        text = pyperclip.paste()
        return text if isinstance(text, str) and text.strip() else None

    def write_text(self, text: str) -> None:
        """Copy text to the system clipboard."""
        if pyperclip is None:
            raise RuntimeError("pyperclip is not installed.")
        pyperclip.copy(text)

    def watch(self, on_change: Callable[[str], None]) -> None:
        """Poll for clipboard changes and call `on_change` for new text."""
        previous: str | None = None
        while True:
            current = self.read_current()
            if current and current != previous:
                on_change(current)
                previous = current
            time.sleep(self.poll_interval_seconds)
