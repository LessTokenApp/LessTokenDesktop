"""Watch the clipboard for new images and shrink them in place.

The point is to collapse the manual loop - paste, shrink, copy the result -
into nothing: take a screenshot, and the clipboard already holds the small
version by the time you paste it.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Hashing a 4K frame every tick is wasteful, and we only need to answer "is
# this the same picture as last time", so fingerprint a thumbnail instead.
_FINGERPRINT_SIZE = (64, 64)


@dataclass(frozen=True)
class AutoShrinkResult:
    original_size: tuple[int, int]
    new_size: tuple[int, int]
    new_bytes: int
    copied: bool


def fingerprint(image) -> str:
    """Return a cheap, stable identifier for an image's visible content."""
    thumb = image.convert("RGB").resize(_FINGERPRINT_SIZE)
    digest = hashlib.sha1(thumb.tobytes()).hexdigest()
    return f"{image.size[0]}x{image.size[1]}:{digest}"


class ClipboardImageWatcher:
    """Shrink clipboard images as they appear.

    Callers drive this by calling `poll()` on a timer, so it stays compatible
    with a Tk event loop rather than owning a blocking thread.
    """

    def __init__(self, optimizer, on_result=None, on_error=None) -> None:
        self.optimizer = optimizer
        self.on_result = on_result
        self.on_error = on_error
        self.enabled = False
        self.max_width = 1024
        self.quality = 80
        self.fmt = "JPEG"
        # Fingerprints we must not react to: the last thing we saw, and the
        # last thing we wrote. Without the second one we would re-shrink our
        # own output on the next tick, forever.
        self._seen: str | None = None
        self._written: str | None = None

    def prime(self) -> None:
        """Adopt whatever is on the clipboard now without shrinking it.

        Called when the watcher is switched on, so enabling the feature does
        not retroactively rewrite an image the user already had.
        """
        image = self._grab()
        self._seen = fingerprint(image) if image is not None else None

    def poll(self) -> AutoShrinkResult | None:
        """Shrink the clipboard image if it is new. Returns None otherwise."""
        if not self.enabled:
            return None

        image = self._grab()
        if image is None:
            return None

        try:
            current = fingerprint(image)
        except Exception as exc:  # a malformed clipboard payload
            logger.debug("Could not fingerprint clipboard image: %s", exc)
            return None

        if current in (self._seen, self._written):
            return None

        self._seen = current

        try:
            result = self.optimizer.save_resized(
                image, max_width=self.max_width, quality=self.quality, fmt=self.fmt
            )
            copied = self.optimizer.copy_image_to_clipboard(result.path)
        except Exception as exc:
            logger.exception("Auto-shrink failed")
            if self.on_error:
                self.on_error(exc)
            return None

        if copied:
            written = self._grab()
            if written is not None:
                try:
                    self._written = fingerprint(written)
                    self._seen = self._written
                except Exception:  # pragma: no cover - defensive
                    self._written = None
        else:
            logger.warning("Resized image saved but could not be put on the clipboard")

        outcome = AutoShrinkResult(
            original_size=result.original_size,
            new_size=result.new_size,
            new_bytes=result.new_bytes,
            copied=copied,
        )
        if self.on_result:
            self.on_result(outcome)
        return outcome

    def _grab(self):
        try:
            return self.optimizer.get_clipboard_image()
        except Exception as exc:
            # Another process can hold the clipboard open; that is routine.
            logger.debug("Clipboard read failed: %s", exc)
            return None
