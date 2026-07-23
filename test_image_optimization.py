"""Test image optimization functionality."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PIL import Image, ImageDraw, ImageFont
from aiclipboardoptimizer.services.image import ImageService
from aiclipboardoptimizer.core.logger import Logger

# Setup logging
Logger.configure("INFO")
logger = Logger.get(__name__)


def create_test_image(path: Path, width: int = 4000, height: int = 2500) -> Path:
    """Create a test image with text."""
    logger.info(f"Creating test image: {width}x{height}")

    # Create image with gradient
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw colored rectangles
    colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
    rect_width = width // len(colors)

    for i, color in enumerate(colors):
        x1 = i * rect_width
        y1 = 0
        x2 = x1 + rect_width
        y2 = height // 2
        draw.rectangle([x1, y1, x2, y2], fill=color)

    # Add text
    text = "AI Clipboard Optimizer - Image Optimization Test"
    try:
        draw.text((width // 2 - 200, height // 2), text, fill='black')
    except:
        pass  # Font might not be available

    # Save as high-quality JPEG
    img.save(path, 'JPEG', quality=95)
    logger.info(f"Test image created: {path}")

    return path


def test_image_optimization():
    """Test image optimization."""
    # Create test directory
    test_dir = Path(__file__).parent / ".test_images"
    test_dir.mkdir(exist_ok=True)

    # Create test image
    original_path = test_dir / "original_4k.jpg"
    create_test_image(original_path, width=4000, height=2500)

    # Get original size
    original_size = original_path.stat().st_size
    logger.info(f"\n{'='*60}")
    logger.info(f"ORIGINAL IMAGE")
    logger.info(f"{'='*60}")
    logger.info(f"File: {original_path.name}")
    logger.info(f"Size: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)")
    logger.info(f"Dimensions: 4000×2500")

    # Estimate tokens
    pixels = 4000 * 2500
    tokens_original = int(pixels * 0.01)  # ~1 token per 100 pixels
    logger.info(f"Estimated Tokens: {tokens_original:,}")

    # Initialize service
    service = ImageService()
    logger.info(f"\n{'='*60}")
    logger.info(f"OPTIMIZING IMAGE")
    logger.info(f"{'='*60}")

    # Test different optimization levels
    test_cases = [
        {
            "name": "Ultra Low Quality (Draft)",
            "max_width": 800,
            "max_height": 600,
            "quality": 40,
        },
        {
            "name": "Low Quality (Mobile)",
            "max_width": 1024,
            "max_height": 768,
            "quality": 60,
        },
        {
            "name": "Medium Quality (Recommended)",
            "max_width": 1600,
            "max_height": 1200,
            "quality": 75,
        },
        {
            "name": "High Quality",
            "max_width": 2560,
            "max_height": 1920,
            "quality": 85,
        },
    ]

    results = []

    for test_case in test_cases:
        logger.info(f"\nTest: {test_case['name']}")
        logger.info(f"Settings: {test_case['max_width']}x{test_case['max_height']}, Q={test_case['quality']}")

        result = service.optimize(
            image_path=original_path,
            max_width=test_case["max_width"],
            max_height=test_case["max_height"],
            quality=test_case["quality"],
            extract_text=False,
        )

        results.append((test_case["name"], result))

        # Save optimized image
        opt_path = test_dir / f"optimized_{test_case['max_width']}x{test_case['max_height']}_q{test_case['quality']}.jpg"
        result.optimized_image.save(opt_path, 'JPEG', quality=test_case['quality'], optimize=True)

        logger.info(f"  → Size: {result.optimized_size_bytes:,} bytes ({result.optimized_size_bytes / 1024:.1f} KB)")
        logger.info(f"  → Dimensions: {result.optimized_dimensions[0]}×{result.optimized_dimensions[1]}")
        logger.info(f"  → Size Savings: {result.size_savings:.1f}%")
        logger.info(f"  → Token Savings: {result.token_savings:.1f}%")
        logger.info(f"  → Tokens: {result.token_estimate_original:,} → {result.token_estimate_optimized:,}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Original: {original_size / 1024 / 1024:.2f} MB ({tokens_original:,} tokens)\n")

    for name, result in results:
        savings_pct = result.size_savings
        token_savings_pct = result.token_savings
        logger.info(
            f"{name:.<40} "
            f"{result.optimized_size_bytes / 1024:>6.1f} KB | "
            f"Size: {savings_pct:>5.1f}% | "
            f"Tokens: {token_savings_pct:>5.1f}%"
        )

    # Best result
    best_result = max(results, key=lambda x: x[1].token_savings)
    logger.info(f"\n{'='*60}")
    logger.info(f"BEST OPTIMIZATION: {best_result[0]}")
    logger.info(f"Token Savings: {best_result[1].token_savings:.1f}%")
    logger.info(f"File Size Reduction: {best_result[1].size_savings:.1f}%")
    logger.info(f"Cost Comparison:")
    logger.info(f"  Original: ${tokens_original * 0.0000025:.6f} (GPT-4o pricing)")
    logger.info(f"  Optimized: ${best_result[1].token_estimate_optimized * 0.0000025:.6f}")
    logger.info(f"  Savings: ${(tokens_original - best_result[1].token_estimate_optimized) * 0.0000025:.6f}")
    logger.info(f"{'='*60}\n")

    # Cleanup
    import shutil
    # shutil.rmtree(test_dir)  # Uncomment to clean up test images
    logger.info(f"Test images saved in: {test_dir}")

    return results


if __name__ == "__main__":
    try:
        results = test_image_optimization()
        print("\n✅ Test tamamlandı!")
    except Exception as e:
        print(f"\n❌ Test başarısız: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
