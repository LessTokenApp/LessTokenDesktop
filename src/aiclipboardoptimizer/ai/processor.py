"""Text processing with multi-provider support and local fallbacks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from pathlib import Path

from .analyzer import PromptAnalyzer
from .cache import PromptCache
from .providers import ProviderFactory
from .router import ModelRouter
from .token_tracker import TokenTracker, TokenUsage
from aiclipboardoptimizer.utils.text import normalize_whitespace


@dataclass(frozen=True)
class TextOperation:
    key: str
    label: str
    instruction: str


OPERATIONS: tuple[TextOperation, ...] = (
    TextOperation("clean", "Duzelt / temizle", "Clean up spelling, grammar, and clarity."),
    TextOperation("shorten", "Daha kisa yap", "Make the text shorter without losing the point."),
    TextOperation("formal", "Daha resmi yap", "Rewrite the text in a professional formal tone."),
    TextOperation("summarize", "Ozetle", "Summarize the text clearly in Turkish."),
    TextOperation("bullets", "Madde madde yap", "Turn the text into concise bullet points in Turkish."),
    TextOperation("translate_en", "Ingilizceye cevir", "Translate the text into natural English."),
    TextOperation("email", "E-posta haline getir", "Turn the text into a polished email draft."),
)


class AIProcessor:
    """Run text operations through multi-provider LLM support with local fallbacks."""

    def __init__(
        self,
        provider: str = "local",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        tracking_enabled: bool = True,
        caching_enabled: bool = True,
        quality_level: str = "balanced",
    ) -> None:
        self.provider_name = provider.lower().strip()
        self.model = model
        self.api_key = api_key
        self.quality_level = quality_level

        # Initialize provider (lazy - may raise on actual use if not configured)
        try:
            self.provider = ProviderFactory.create(self.provider_name, api_key)
        except ValueError:
            self.provider = None

        self.analyzer = PromptAnalyzer()
        self.tracker = TokenTracker() if tracking_enabled else None
        self.cache = PromptCache() if caching_enabled else None
        self.router = ModelRouter(default_provider=self.provider_name, quality_level=quality_level)

    @property
    def is_ai_enabled(self) -> bool:
        """Check if AI provider is available and configured."""
        return self.provider is not None and self.provider_name != "local"

    def optimize_text(self, text: str, operation: str = "clean") -> str:
        """Process text with the selected operation."""
        source = text.strip()
        if not source:
            return ""

        selected = self._get_operation(operation)

        if self.is_ai_enabled:
            try:
                return self._run_ai(source, selected)
            except Exception as exc:
                local_result = self._run_local(source, selected.key)
                return f"AI kullanilamadi, yerel sonuc verildi. ({exc})\n\n{local_result}"

        return self._run_local(source, selected.key)

    def _run_ai(self, text: str, operation: TextOperation) -> str:
        """Execute through AI provider with caching, optimization, and routing."""
        prompt = (
            f"{operation.instruction}\n"
            "Return only the final text. Keep the user's language unless translation is requested.\n\n"
            f"Text:\n{text}"
        )

        # Select optimal model using router
        recommendation = self.router.recommend_model(len(text), operation.key, self.provider_name)
        selected_model = recommendation.model

        # Check cache first
        if self.cache:
            cached = self.cache.get(prompt, self.provider_name, selected_model)
            if cached:
                # Track cache hit
                if self.tracker:
                    usage = TokenUsage(
                        provider=self.provider_name,
                        model=selected_model,
                        input_tokens=0,  # Cache hit doesn't consume tokens
                        output_tokens=0,
                        cost_usd=0.0,
                        timestamp=datetime.now(),
                        operation=f"{operation.key} (cache hit)",
                        source_length=len(text),
                    )
                    self.tracker.track(usage)
                return cached.result_text

        # Analyze prompt for optimization
        analysis = self.analyzer.analyze(prompt, selected_model)
        if analysis.savings_percent > 15:
            prompt = analysis.optimized_text

        # Execute through provider with selected model
        response = self.provider.process(prompt, selected_model)

        # Cache result
        if self.cache:
            self.cache.set(
                prompt=prompt,
                result_text=response.text,
                provider=self.provider_name,
                model=selected_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
            )

        # Track usage with router recommendation info
        if self.tracker:
            usage = TokenUsage(
                provider=self.provider_name,
                model=selected_model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
                timestamp=datetime.now(),
                operation=operation.key,
                source_length=len(text),
            )
            self.tracker.track(usage)

        return response.text.strip()

    def _run_local(self, text: str, operation: str) -> str:
        """Execute local regex-based fallback."""
        cleaned = normalize_whitespace(text)
        if operation == "shorten":
            return self._shorten(cleaned)
        if operation == "formal":
            return self._formalize(cleaned)
        if operation == "summarize":
            return self._summarize(cleaned)
        if operation == "bullets":
            return self._bullets(cleaned)
        if operation == "translate_en":
            return "[AI gerekli] Ingilizce ceviri icin OpenAI API anahtari ekleyin.\n\n" + cleaned
        if operation == "email":
            return "Merhaba,\n\n" + cleaned + "\n\nSaygilarimla,"
        return cleaned

    def _get_operation(self, key: str) -> TextOperation:
        return next((item for item in OPERATIONS if item.key == key), OPERATIONS[0])

    def _shorten(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 1:
            return " ".join(sentences[:2]).strip()
        words = text.split()
        return " ".join(words[:40]) + ("..." if len(words) > 40 else "")

    def _formalize(self, text: str) -> str:
        replacements = {
            "selam": "Merhaba",
            "tamam": "uygundur",
            "ok": "uygundur",
            "tesekkurler": "Tesekkur ederim",
        }
        result = text
        for source, target in replacements.items():
            result = re.sub(rf"\b{source}\b", target, result, flags=re.IGNORECASE)
        return result[0].upper() + result[1:] if result else result

    def _summarize(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return " ".join(sentences[:3]).strip()

    def _bullets(self, text: str) -> str:
        parts = [part.strip(" -") for part in re.split(r"(?<=[.!?])\s+|;", text) if part.strip()]
        return "\n".join(f"- {part}" for part in parts[:12])


def get_operation_labels() -> dict[str, str]:
    """Return operation keys and display labels for the UI."""
    return {operation.key: operation.label for operation in OPERATIONS}
