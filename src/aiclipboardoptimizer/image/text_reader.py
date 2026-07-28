"""Read the text in an image, locally when possible and via an AI when not.

Tesseract is preferred when it is installed: it costs nothing and the image
never leaves the machine. Most people will not have it, though, and they have
already configured an AI that can read images - so fall back to that rather
than telling them to go and install an OCR engine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO

logger = logging.getLogger(__name__)

PROMPT = (
    "Extract all readable text from this image. "
    "Return only the text itself, preserving line breaks, with no commentary."
)

# Anything larger is downscaled first: vision models charge by image size and
# gain nothing from a 4K screenshot of a text panel.
MAX_EDGE = 1600


@dataclass(frozen=True)
class ImageTextResult:
    text: str
    source: str  # "tesseract" or a provider name
    cost_usd: float = 0.0


class ImageTextReader:
    """Extract image text, preferring a local engine over a paid API."""

    def __init__(self, optimizer, provider=None) -> None:
        self.optimizer = optimizer
        self.provider = provider

    def read(self, image) -> ImageTextResult:
        local = self._read_locally(image)
        if local is not None:
            return ImageTextResult(text=local, source="tesseract")

        if self.provider is None or not getattr(self.provider, "supports_vision", False):
            return ImageTextResult(
                text=(
                    "Görselden metin okumak için ya Tesseract OCR kurulu olmalı, "
                    "ya da görüntü okuyabilen bir yapay zeka seçili olmalı "
                    "(ChatGPT, Claude veya Gemini)."
                ),
                source="none",
            )

        return self._read_with_ai(image)

    def _read_locally(self, image) -> str | None:
        """Return Tesseract's reading, or None when it is unavailable."""
        try:
            import pytesseract
        except ImportError:
            return None

        try:
            text = pytesseract.image_to_string(image)
        except Exception as exc:
            # Missing engine, missing language data, anything else: the AI path
            # is a better answer than an error.
            logger.info("Local OCR unavailable, falling back to AI: %s", exc)
            return None

        return text.strip() or None

    def _read_with_ai(self, image) -> ImageTextResult:
        payload, media_type = self._encode(image)
        try:
            response = self.provider.read_image(payload, media_type, PROMPT)
        except Exception as exc:
            logger.exception("AI image read failed")
            return ImageTextResult(text=f"Görsel okunamadı: {exc}", source="error")

        return ImageTextResult(
            text=response.text.strip() or "Görselde okunabilir metin bulunamadı.",
            source=self.provider.provider_name,
            cost_usd=response.cost_usd,
        )

    def _encode(self, image) -> tuple[bytes, str]:
        """Return JPEG bytes, downscaled so we do not pay for pixels we
        do not need."""
        prepared = image.convert("RGB")
        longest = max(prepared.size)
        if longest > MAX_EDGE:
            ratio = MAX_EDGE / longest
            prepared = prepared.resize(
                (max(1, int(prepared.width * ratio)), max(1, int(prepared.height * ratio)))
            )

        buffer = BytesIO()
        prepared.save(buffer, "JPEG", quality=85, optimize=True)
        return buffer.getvalue(), "image/jpeg"
