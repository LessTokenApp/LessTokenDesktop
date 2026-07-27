"""Image processing helpers."""

from .optimizer import ImageOptimizer, ImageResult
from .watcher import AutoShrinkResult, ClipboardImageWatcher

__all__ = [
    "AutoShrinkResult",
    "ClipboardImageWatcher",
    "ImageOptimizer",
    "ImageResult",
]
