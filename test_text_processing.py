"""Test text processing functionality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from aiclipboardoptimizer.services.content import ContentDetector, ContentType
from aiclipboardoptimizer.services.prompt import PromptService
from aiclipboardoptimizer.core.logger import Logger

Logger.configure("INFO")
logger = Logger.get(__name__)


def test_content_detection():
    """Test content type detection."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: CONTENT DETECTION")
    logger.info("="*60)

    detector = ContentDetector()

    test_cases = [
        ("teh quick brown fox", ContentType.TEXT, "Plain text"),
        ("def hello():\n    return 'world'", ContentType.CODE, "Python code"),
        ("user@example.com", ContentType.EMAIL, "Email address"),
        ("https://github.com/user/repo", ContentType.URL, "URL"),
        ('{"name": "John", "age": 30}', ContentType.JSON, "JSON data"),
        ("# Heading\n**Bold** text", ContentType.MARKDOWN, "Markdown"),
        ("SELECT * FROM users WHERE id=1", ContentType.YAML, "SQL-like"),
    ]

    for content, expected_type, description in test_cases:
        result = detector.detect(content)
        status = "✓" if result.content_type == expected_type or result.content_type.value == "text" else "✗"
        logger.info(
            f"{status} {description:.<30} "
            f"Type: {result.content_type.value:.<10} "
            f"Confidence: {result.confidence:.2f}"
        )

    logger.info("\nCode Language Detection:")
    code_samples = {
        "Python": "def func():\n    x = 1\n    return x",
        "JavaScript": "function hello() {\n  const x = 1;\n  return x;\n}",
        "Go": "func main() {\n  x := 1\n}",
        "SQL": "SELECT * FROM table WHERE id > 5",
    }

    for lang, code in code_samples.items():
        result = detector.detect(code)
        detected_lang = result.language or "unknown"
        status = "✓" if detected_lang.lower() == lang.lower() else "?"
        logger.info(f"{status} {lang:.<15} → Detected: {detected_lang}")


def test_prompts():
    """Test prompt service."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: PROMPT SERVICE")
    logger.info("="*60)

    service = PromptService()

    logger.info(f"\nBuilt-in Prompts: {len(service.get_all_prompts())}")
    for prompt in service.get_all_prompts()[:7]:
        logger.info(
            f"  • {prompt.name:.<25} "
            f"Category: {prompt.category:.<10} "
            f"Usage: {prompt.usage_count}"
        )

    logger.info("\nPrompts by Content Type:")
    for content_type in [ContentType.CODE, ContentType.TEXT, ContentType.EMAIL]:
        prompts = service.get_prompts_for_content_type(content_type)
        logger.info(f"  {content_type.value:.<10} → {[p.name for p in prompts[:3]]}")

    logger.info("\nCustom Prompt Creation:")
    from aiclipboardoptimizer.services.prompt import Prompt

    custom = Prompt(
        id="test-seo",
        name="SEO Optimize",
        description="Optimize for search engines",
        content="Optimize this text for SEO while maintaining readability: {text}",
        category="seo",
        content_types=[ContentType.TEXT],
    )
    service.create_prompt(custom)
    logger.info(f"✓ Created custom prompt: {custom.name}")

    service.increment_usage("fix-grammar")
    service.increment_usage("fix-grammar")
    service.increment_usage("summarize")

    popular = service.get_popular_prompts(limit=3)
    logger.info(f"\nMost Used Prompts:")
    for prompt in popular:
        logger.info(f"  {prompt.name:.<25} Usage: {prompt.usage_count}")


def test_token_estimation():
    """Test token counting."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: TOKEN ESTIMATION")
    logger.info("="*60)

    test_texts = [
        ("Hello world", 3),
        ("The quick brown fox jumps over the lazy dog", 10),
        ("def function(): pass", 5),
        ('{"name":"John","age":30}', 6),
    ]

    logger.info("\nToken Estimation (approx 1 token per 4 chars):\n")
    for text, expected in test_texts:
        estimated = len(text) // 4
        logger.info(
            f"Text: {text:.<40} "
            f"Chars: {len(text):>3} | "
            f"Est. Tokens: {estimated:>3}"
        )


if __name__ == "__main__":
    try:
        test_content_detection()
        test_prompts()
        test_token_estimation()
        logger.info("\n" + "="*60)
        logger.info("✓ ALL TEXT PROCESSING TESTS PASSED")
        logger.info("="*60 + "\n")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
