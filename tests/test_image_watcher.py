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
    def __init__(self, image, copy_succeeds=True):
        self._image = image
        self._copy_succeeds = copy_succeeds
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
        return self._copy_succeeds


def test_poll_recompresses_even_an_already_small_image() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    watcher = ClipboardImageWatcher(optimizer)
    watcher.enabled = True
    watcher.max_width = 1600

    result = watcher.poll()

    assert result is not None
    assert result.original_size == (200, 100)
    assert result.copied is True
    assert len(optimizer.save_resized_calls) == 1
    assert len(optimizer.copy_calls) == 1


def test_poll_reports_copied_false_when_clipboard_write_fails() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image, copy_succeeds=False)
    watcher = ClipboardImageWatcher(optimizer)
    watcher.enabled = True
    watcher.max_width = 1600

    result = watcher.poll()

    assert result is not None
    assert result.copied is False


def test_poll_does_not_reprocess_the_same_image_twice() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    watcher = ClipboardImageWatcher(optimizer)
    watcher.enabled = True
    watcher.max_width = 1600

    watcher.poll()
    watcher.poll()

    assert len(optimizer.save_resized_calls) == 1
