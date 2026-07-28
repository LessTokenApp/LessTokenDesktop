"""Tests for ClipboardImageWatcher's skip-notification behavior."""
from PIL import Image

from aiclipboardoptimizer.image.watcher import ClipboardImageWatcher


class _FakeOptimizer:
    def __init__(self, image):
        self._image = image

    def get_clipboard_image(self):
        return self._image


def test_poll_notifies_on_skip_for_already_small_image() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    skipped = []
    watcher = ClipboardImageWatcher(optimizer, on_skip=skipped.append)
    watcher.enabled = True
    watcher.max_width = 1600

    result = watcher.poll()

    assert result is None
    assert skipped == [(200, 100)]


def test_poll_does_not_notify_skip_twice_for_the_same_image() -> None:
    small_image = Image.new("RGB", (200, 100), color="white")
    optimizer = _FakeOptimizer(small_image)
    skipped = []
    watcher = ClipboardImageWatcher(optimizer, on_skip=skipped.append)
    watcher.enabled = True
    watcher.max_width = 1600

    watcher.poll()
    watcher.poll()

    assert skipped == [(200, 100)]
