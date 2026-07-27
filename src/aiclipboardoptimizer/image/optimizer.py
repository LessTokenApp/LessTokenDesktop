"""Image clipboard and compression helpers."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from time import strftime

try:
    from PIL import Image, ImageGrab
except ImportError:  # pragma: no cover - optional dependency
    Image = None
    ImageGrab = None


@dataclass(frozen=True)
class ImageResult:
    path: Path
    original_size: tuple[int, int]
    new_size: tuple[int, int]
    original_bytes: int | None
    new_bytes: int


class ImageOptimizer:
    """Resize, compress, and inspect images."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_clipboard_image(self):
        """Return a PIL image from the clipboard, or None if none exists."""
        self._require_pillow()
        grabbed = ImageGrab.grabclipboard()
        if grabbed is None:
            return None
        if isinstance(grabbed, list) and grabbed:
            return Image.open(grabbed[0])
        return grabbed if hasattr(grabbed, "size") else None

    def open_image(self, path: str | Path):
        """Open an image file."""
        self._require_pillow()
        return Image.open(path)

    def save_resized(self, image, max_width: int, quality: int, fmt: str) -> ImageResult:
        """Resize and save an image to the output directory."""
        self._require_pillow()
        original_size = image.size
        resized = image.copy()
        if max_width > 0 and resized.width > max_width:
            ratio = max_width / resized.width
            new_height = max(1, int(resized.height * ratio))
            resized = resized.resize((max_width, new_height), Image.Resampling.LANCZOS)

        fmt = fmt.upper()
        extension = "jpg" if fmt == "JPEG" else fmt.lower()
        output_path = self.output_dir / f"optimized_{strftime('%Y%m%d_%H%M%S')}.{extension}"

        save_image = resized.convert("RGB") if fmt in {"JPEG", "WEBP"} else resized
        save_kwargs = {"quality": quality, "optimize": True} if fmt in {"JPEG", "WEBP"} else {"optimize": True}
        save_image.save(output_path, fmt, **save_kwargs)

        return ImageResult(
            path=output_path,
            original_size=original_size,
            new_size=resized.size,
            original_bytes=None,
            new_bytes=output_path.stat().st_size,
        )

    def copy_image_to_clipboard(self, image_path: str | Path) -> bool:
        """Copy an image to the Windows clipboard when pywin32 is available."""
        try:
            import win32clipboard
            import win32con
        except ImportError:
            return False

        self._require_pillow()
        image = Image.open(image_path).convert("RGB")
        output = BytesIO()
        image.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()
        return True

    def extract_text(self, image) -> str:
        """Extract text with pytesseract if it is installed."""
        try:
            import pytesseract
        except ImportError:
            return "OCR icin pytesseract ve Tesseract OCR kurulumu gerekir."

        try:
            text = pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            # pytesseract is only a wrapper: the engine is a separate install,
            # and its absence surfaces here rather than at import time.
            return (
                "OCR icin Tesseract OCR programi gerekir. "
                "https://github.com/UB-Mannheim/tesseract adresinden kurabilirsiniz."
            )

        return text.strip() or "Gorselde okunabilir metin bulunamadi."

    def describe_image(self, image) -> str:
        """Return a local technical description of an image."""
        width, height = image.size
        return f"Gorsel bilgisi: {width}x{height} piksel, mod: {image.mode}."

    def _require_pillow(self) -> None:
        if Image is None or ImageGrab is None:
            raise RuntimeError("Gorsel islemleri icin Pillow paketi kurulu olmali.")
