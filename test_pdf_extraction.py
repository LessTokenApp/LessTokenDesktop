"""Test PDF extraction functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from aiclipboardoptimizer.services.file import FileService
from aiclipboardoptimizer.core.logger import Logger

Logger.configure("INFO")
logger = Logger.get(__name__)


def create_test_pdf(path: Path, num_pages: int = 5) -> Path:
    """Create a test PDF file."""
    logger.info(f"Creating test PDF: {num_pages} pages")

    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter

    for page_num in range(1, num_pages + 1):
        c.setFont("Helvetica", 24)
        c.drawString(50, height - 50, f"Test Document - Page {page_num}")

        c.setFont("Helvetica", 12)
        y_pos = height - 100

        sample_text = f"""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Page {page_num}.

This is a test PDF document for testing extraction functionality.
Each page contains some sample text to demonstrate token counting.

Key points about this page:
- This is point one
- This is point two
- This is point three
- This is point four
- This is point five

The content continues with more lorem ipsum text to fill the page.
This helps us estimate token counts accurately.
        """

        for line in sample_text.split('\n'):
            if y_pos < 50:
                break
            c.drawString(50, y_pos, line)
            y_pos -= 15

        c.showPage()

    c.save()
    logger.info(f"Test PDF created: {path}")
    return path


def test_pdf_extraction():
    """Test PDF extraction."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: PDF EXTRACTION")
    logger.info("="*60)

    # Create test PDF
    test_dir = Path(__file__).parent / ".test_pdfs"
    test_dir.mkdir(exist_ok=True)
    pdf_path = test_dir / "test_document.pdf"

    create_test_pdf(pdf_path, num_pages=10)

    # Initialize service
    service = FileService()

    # Test 1: Extract all pages
    logger.info("\nTest: Extract All Pages")
    result = service.extract(pdf_path)

    logger.info(f"  File: {result.file_path.name}")
    logger.info(f"  Type: {result.file_type}")
    logger.info(f"  Total Pages: {result.total_pages}")
    logger.info(f"  Total Chars: {result.total_chars:,}")
    logger.info(f"  Total Words: {result.total_words:,}")
    logger.info(f"  Est. Tokens: {result.token_estimate:,}")
    logger.info(f"  Content Preview: {result.text_summary[:80]}...")

    # Test 2: Extract specific pages
    logger.info("\nTest: Extract Specific Pages (1-3)")
    result_partial = service.extract(pdf_path, pages=[1, 2, 3])

    logger.info(f"  Pages Extracted: {len(result_partial.pages_extracted)}")
    logger.info(f"  Chars: {result_partial.total_chars:,}")
    logger.info(f"  Est. Tokens: {result_partial.token_estimate:,}")
    logger.info(f"  Reduction: {(1 - result_partial.token_estimate / result.token_estimate) * 100:.1f}%")

    # Test 3: Cost estimation
    logger.info("\nTest: Cost Estimation")
    tokens = result.token_estimate
    cost_openai = (tokens / 1_000_000) * 0.0000025  # GPT-4o pricing
    cost_claude = (tokens / 1_000_000) * 0.000003   # Claude pricing
    cost_gemini = (tokens / 1_000_000) * 0.0000005  # Gemini pricing
    cost_ollama = 0  # Free

    logger.info(f"  Tokens: {tokens:,}")
    logger.info(f"  OpenAI (GPT-4o): ${cost_openai:.6f}")
    logger.info(f"  Claude (3.5-haiku): ${cost_claude:.6f}")
    logger.info(f"  Gemini (2.5-flash): ${cost_gemini:.6f}")
    logger.info(f"  Ollama (local): ${cost_ollama:.6f}")

    logger.info("\n" + "="*60)
    logger.info("PDF EXTRACTION TEST PASSED")
    logger.info("="*60 + "\n")

    return result


if __name__ == "__main__":
    try:
        test_pdf_extraction()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
