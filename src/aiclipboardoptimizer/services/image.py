"""Image processing and optimization service."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import io

from PIL import Image
import pytesseract

from .base import BaseService
from .content import ContentType, ContentInfo
from ..core.logger import Logger

logger = Logger.get(__name__)


@dataclass
class ImageOptimizationResult:
    """Result of image optimization."""
    original_path: Path
    original_size_bytes: int
    original_dimensions: Tuple[int, int]
    optimized_size_bytes: int
    optimized_dimensions: Tuple[int, int]
    optimized_image: Image.Image
    compression_ratio: float  # 0.0-1.0, lower = more compressed
    extracted_text: Optional[str] = None
    token_estimate_original: int = 0
    token_estimate_optimized: int = 0

    @property
    def token_savings(self) -> float:
        """Token savings percentage."""
        if self.token_estimate_original == 0:
            return 0.0
        return (
            (self.token_estimate_original - self.token_estimate_optimized)
            / self.token_estimate_original
            * 100
        )

    @property
    def size_savings(self) -> float:
        """File size savings percentage."""
        if self.original_size_bytes == 0:
            return 0.0
        return (
            (self.original_size_bytes - self.optimized_size_bytes)
            / self.original_size_bytes
            * 100
        )


class ImageService(BaseService):
    """Service for image processing and optimization."""

    # Token estimation: ~1 token per 100 pixels (rough estimate)
    TOKENS_PER_PIXEL = 0.01

    # Supported formats
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

    # Default optimization settings
    DEFAULT_MAX_WIDTH = 1024
    DEFAULT_MAX_HEIGHT = 768
    DEFAULT_JPEG_QUALITY = 60

    def __init__(self):
        self._ocr_available = self._check_ocr()

    @property
    def service_name(self) -> str:
        return "image"

    def _check_ocr(self) -> bool:
        """Check if pytesseract is available."""
        try:
            # Try to get Tesseract version
            pytesseract.get_tesseract_version()
            logger.info("OCR (Tesseract) available")
            return True
        except Exception:
            logger.warning("OCR (Tesseract) not available - install tesseract-ocr")
            return False

    def optimize(
        self,
        image_path: Path,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
        extract_text: bool = False,
    ) -> ImageOptimizationResult:
        """Optimize image for token reduction.

        Args:
            image_path: Path to image file
            max_width: Maximum width (default 1024)
            max_height: Maximum height (default 768)
            quality: JPEG quality 1-95 (default 60)
            extract_text: Whether to extract text via OCR

        Returns:
            ImageOptimizationResult with metrics

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If format not supported
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {image_path.suffix}")

        # Get original size
        original_size_bytes = image_path.stat().st_size

        # Load image
        try:
            img = Image.open(image_path)
            original_dims = img.size
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            raise

        # Set defaults
        max_w = max_width or self.DEFAULT_MAX_WIDTH
        max_h = max_height or self.DEFAULT_MAX_HEIGHT
        qual = quality or self.DEFAULT_JPEG_QUALITY

        logger.info(
            f"Optimizing image: {original_dims[0]}×{original_dims[1]} → "
            f"max {max_w}×{max_h}, quality={qual}"
        )

        # Resize if needed
        optimized_img = self._resize_image(img, max_w, max_h)
        optimized_dims = optimized_img.size

        # Compress and save to bytes
        optimized_bytes = self._compress_image(optimized_img, qual)
        optimized_size_bytes = len(optimized_bytes)

        # Extract text if requested
        extracted_text = None
        if extract_text and self._ocr_available:
            try:
                extracted_text = pytesseract.image_to_string(optimized_img)
                logger.debug(f"Extracted {len(extracted_text)} chars via OCR")
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")

        # Calculate token estimates
        orig_pixels = original_dims[0] * original_dims[1]
        opt_pixels = optimized_dims[0] * optimized_dims[1]

        token_orig = int(orig_pixels * self.TOKENS_PER_PIXEL)
        token_opt = int(opt_pixels * self.TOKENS_PER_PIXEL)

        # If OCR extracted text, add text tokens (~1 token per 4 chars)
        if extracted_text:
            text_tokens = len(extracted_text) // 4
            token_opt += text_tokens

        compression_ratio = optimized_size_bytes / original_size_bytes

        result = ImageOptimizationResult(
            original_path=image_path,
            original_size_bytes=original_size_bytes,
            original_dimensions=original_dims,
            optimized_size_bytes=optimized_size_bytes,
            optimized_dimensions=optimized_dims,
            optimized_image=optimized_img,
            compression_ratio=compression_ratio,
            extracted_text=extracted_text,
            token_estimate_original=token_orig,
            token_estimate_optimized=token_opt,
        )

        logger.info(
            f"Optimization complete: "
            f"{original_size_bytes:,}B → {optimized_size_bytes:,}B "
            f"({compression_ratio*100:.1f}%), "
            f"Tokens: {token_orig:,} → {token_opt:,} ({result.token_savings:.1f}% savings)"
        )

        return result

    def optimize_from_bytes(
        self,
        image_bytes: bytes,
        format: str = "JPEG",
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: Optional[int] = None,
    ) -> bytes:
        """Optimize image from bytes (e.g., clipboard).

        Args:
            image_bytes: Image data
            format: Output format (JPEG, PNG, WebP)
            max_width: Maximum width
            max_height: Maximum height
            quality: Quality setting

        Returns:
            Optimized image bytes
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))

            max_w = max_width or self.DEFAULT_MAX_WIDTH
            max_h = max_height or self.DEFAULT_MAX_HEIGHT
            qual = quality or self.DEFAULT_JPEG_QUALITY

            # Resize
            optimized_img = self._resize_image(img, max_w, max_h)

            # Compress
            return self._compress_image(optimized_img, qual, format)

        except Exception as e:
            logger.error(f"Failed to optimize image bytes: {e}")
            raise

    def batch_optimize(
        self,
        image_dir: Path,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> list[ImageOptimizationResult]:
        """Optimize all images in directory.

        Args:
            image_dir: Directory containing images
            output_dir: Where to save optimized images
            **kwargs: Arguments for optimize()

        Returns:
            List of optimization results
        """
        image_dir = Path(image_dir)
        output_dir = Path(output_dir or image_dir / "optimized")
        output_dir.mkdir(exist_ok=True)

        results = []

        for image_file in image_dir.glob("*"):
            if image_file.suffix.lower() not in self.SUPPORTED_FORMATS:
                continue

            try:
                result = self.optimize(image_file, **kwargs)
                # Save optimized image
                output_path = output_dir / image_file.name
                result.optimized_image.save(
                    output_path,
                    quality=self.DEFAULT_JPEG_QUALITY,
                    optimize=True,
                )
                logger.debug(f"Saved optimized image: {output_path}")
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to optimize {image_file}: {e}")

        logger.info(f"Batch optimization complete: {len(results)} images")
        return results

    def _resize_image(self, img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Resize image to fit within max dimensions."""
        original_width, original_height = img.size

        # Calculate scaling factor
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale = min(width_ratio, height_ratio, 1.0)  # Don't upscale

        if scale == 1.0:
            return img  # Already small enough

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _compress_image(
        self,
        img: Image.Image,
        quality: int,
        format: str = "JPEG",
    ) -> bytes:
        """Compress image to bytes."""
        output = io.BytesIO()

        # Convert RGBA to RGB for JPEG
        if img.mode == "RGBA" and format.upper() == "JPEG":
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img

        # Save with compression
        img.save(
            output,
            format=format.upper(),
            quality=quality,
            optimize=True,
        )

        return output.getvalue()

    def get_image_info(self, image_path: Path) -> ContentInfo:
        """Get information about image."""
        try:
            img = Image.open(image_path)
            dims = img.size
            size_mb = image_path.stat().st_size / (1024 * 1024)

            return ContentInfo(
                content_type=ContentType.IMAGE,
                content=str(image_path),
                metadata={
                    "dimensions": dims,
                    "format": img.format,
                    "size_mb": size_mb,
                    "mode": img.mode,
                },
            )

        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            raise

    def on_startup(self) -> None:
        """Initialize image service."""
        ocr_status = "available" if self._ocr_available else "unavailable"
        logger.info(f"Image service started - OCR {ocr_status}")

    def on_shutdown(self) -> None:
        """Shutdown image service."""
        logger.info("Image service stopped")
