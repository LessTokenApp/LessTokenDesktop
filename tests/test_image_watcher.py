"""Tests for ClipboardImageWatcher's always-recompress behavior."""
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from aiclipboardoptimizer.image.watcher import ClipboardImageWatcher


@dataclass
class _FakeImageResult:
    path: Path
    original_size: tuple
    new_size: tuple
    original_bytes: int | None
    new_bytes: int


class _FakeOptimizer:
    def __init__(self, image):
        self._image = image
        self.save_resized_calls = []
        self.copy_calls = []

    def get_clipboard_image(self):
        return self._image

    def save_resized(self, image, max_width, quality, fmt):
        self.save_resized_calls.append(image)
        return _FakeImageResult(
            path=Path("fake.jpg"),
            original_size=image.size,
            new_size=image.size,
            original_bytes=None,
            new_bytes=12345,
        )

    def copy_image_to_clipboard(self, path):
        self.copy_calls.append(path)
        return True


def test_poll_recompresses_even_an_already_small_image() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    watcher = ClipboardImageWatcher(optimizer)
    watcher.enabled = True
    watcher.max_width = 1600

    result = watcher.poll()

    assert result is not None
    assert result.original_size == (200, 100)
    assert len(optimizer.save_resized_calls) == 1
    assert len(optimizer.copy_calls) == 1


def test_poll_does_not_reprocess_the_same_image_twice() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    watcher = ClipboardImageWatcher(optimizer)
    watcher.enabled = True
    watcher.max_width = 1600

    watcher.poll()
    watcher.poll()

    assert len(optimizer.save_resized_calls) == 1
