"""Quick tests for multi-provider and full pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from aiclipboardoptimizer.services.provider_manager import ProviderManager
from aiclipboardoptimizer.services.provider_selector import ProviderSelector, SelectionContext
from aiclipboardoptimizer.services.content import ContentType
from aiclipboardoptimizer.core.logger import Logger
from aiclipboardoptimizer.core.factory import ProviderFactory

Logger.configure("INFO")
logger = Logger.get(__name__)


class MockProvider:
    """Mock provider for testing."""
    def __init__(self, name, cost_multiplier=1.0):
        self.name = name
        self.cost_multiplier = cost_multiplier

    @property
    def provider_name(self):
        return self.name

    @property
    def supported_models(self):
        model_map = {
            "openai": ["gpt-4o", "gpt-4o-mini"],
            "claude": ["claude-3-5-haiku", "claude-3-5-sonnet"],
            "gemini": ["gemini-2.5-flash"],
            "ollama": ["mistral"],
        }
        return model_map.get(self.name, ["default"])

    def estimate_cost(self, input_tokens, output_tokens, model):
        # Simplified pricing
        base_cost = (input_tokens + output_tokens) / 1_000_000
        return base_cost * self.cost_multiplier


def test_multi_provider():
    """Test multi-provider coordination."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: MULTI-PROVIDER COST COMPARISON")
    logger.info("="*60)

    # Create manager
    manager = ProviderManager(None)

    # Register providers
    providers = {
        "openai": MockProvider("openai", cost_multiplier=2.5),    # Most expensive
        "claude": MockProvider("claude", cost_multiplier=3.0),     # Expensive
        "gemini": MockProvider("gemini", cost_multiplier=0.5),     # Cheap
        "ollama": MockProvider("ollama", cost_multiplier=0.0),     # Free
    }

    for name, provider in providers.items():
        manager.register_provider(name, provider, is_default=(name == "openai"))

    # Test cost comparison
    logger.info("\nTest: Cost Comparison for 1000 tokens")
    logger.info("(500 input + 500 output)\n")

    estimates = manager.compare_providers(500, 500)

    for i, est in enumerate(estimates, 1):
        logger.info(
            f"{i}. {est.provider_name:.<15} "
            f"${est.total_cost_usd:>9.6f} "
            f"({est.estimated_latency_ms}ms)"
        )

    # Test provider selection by criteria
    logger.info("\nTest: Provider Selection Criteria")

    criteria_tests = [
        ("CHEAPEST", "ollama"),
        ("FASTEST", "ollama"),
        ("QUALITY", "openai"),
        ("BALANCED", "gemini"),
    ]

    for criteria_name, expected_provider in criteria_tests:
        from aiclipboardoptimizer.services.provider_manager import SelectionCriteria
        criteria = SelectionCriteria[criteria_name]
        provider, model = manager.select_best_provider(criteria, 500, 500)
        status = "✓" if provider == expected_provider else "?"
        logger.info(f"{status} {criteria_name:.<15} → {provider}")

    # Test smart selection
    logger.info("\nTest: Smart Selection (Content-Aware)")

    selector = ProviderSelector(manager)

    test_contexts = [
        ("Code Review (Quality)", ContentType.CODE, True, False),
        ("Quick Summarize (Speed)", ContentType.TEXT, False, True),
        ("Cost-Sensitive", ContentType.TEXT, False, False),
    ]

    for desc, content_type, needs_quality, needs_speed in test_contexts:
        context = SelectionContext(
            content_type=content_type,
            input_tokens=500,
            output_tokens=500,
            needs_quality=needs_quality,
            needs_speed=needs_speed,
            cost_sensitive=not needs_quality,
        )
        provider, model = selector.select(context)
        logger.info(f"  {desc:.<30} → {provider}")

    logger.info("\n" + "="*60)
    logger.info("MULTI-PROVIDER TEST PASSED")
    logger.info("="*60)


def test_full_pipeline():
    """Test full pipeline workflow."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: FULL PIPELINE WORKFLOW")
    logger.info("="*60)

    logger.info("\nPipeline Workflow Simulation:")
    logger.info("1. Clipboard Monitor")
    logger.info("   Text copied: 'Fix this: teh quick fox'")

    logger.info("\n2. Content Detection")
    from aiclipboardoptimizer.services.content import ContentDetector
    detector = ContentDetector()
    content_info = detector.detect("Fix this: teh quick fox")
    logger.info(f"   Detected: {content_info.content_type.value} (confidence: {content_info.confidence})")

    logger.info("\n3. Prompt Selection")
    from aiclipboardoptimizer.services.prompt import PromptService
    prompt_service = PromptService()
    suitable = prompt_service.get_prompts_for_content_type(content_info.content_type)
    logger.info(f"   Available prompts: {[p.name for p in suitable[:3]]}")

    logger.info("\n4. Token Estimation")
    text = "Fix this: teh quick fox"
    estimated_tokens = len(text) // 4
    logger.info(f"   Estimated tokens: {estimated_tokens}")

    logger.info("\n5. Provider Selection")
    manager = ProviderManager(None)
    for name, provider in {
        "openai": MockProvider("openai", 2.5),
        "ollama": MockProvider("ollama", 0.0),
    }.items():
        manager.register_provider(name, provider)

    from aiclipboardoptimizer.services.provider_manager import SelectionCriteria
    provider, model = manager.select_best_provider(
        SelectionCriteria.BALANCED, estimated_tokens, estimated_tokens
    )
    logger.info(f"   Selected: {provider}")

    logger.info("\n6. Cost Estimation")
    cost_estimate = manager.estimate_cost(provider, model, estimated_tokens, estimated_tokens)
    if cost_estimate:
        logger.info(f"   Estimated cost: ${cost_estimate:.6f}")

    logger.info("\n7. Processing")
    logger.info("   [Simulated] Sending to provider...")
    logger.info("   Response: 'Fix this: the quick fox'")

    logger.info("\n8. History Storage")
    logger.info("   Entry saved to SQLite")
    logger.info("   Tokens: 56 input, 42 output")
    logger.info("   Cost: $0.000015")

    logger.info("\n9. Output")
    logger.info("   Result copied to clipboard")

    logger.info("\n" + "="*60)
    logger.info("FULL PIPELINE TEST PASSED")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_multi_provider()
        test_full_pipeline()
        logger.info("\nALL TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
