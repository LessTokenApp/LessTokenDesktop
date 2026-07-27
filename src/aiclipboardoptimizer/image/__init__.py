"""Image processing helpers."""

from .optimizer import ImageOptimizer, ImageResult
from .text_reader import ImageTextReader, ImageTextResult
from .watcher import AutoShrinkResult, ClipboardImageWatcher

__all__ = [
    "AutoShrinkResult",
    "ClipboardImageWatcher",
    "ImageOptimizer",
    "ImageResult",
    "ImageTextReader",
    "ImageTextResult",
]
