"""Prompt analysis and optimization for token cost reduction."""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OptimizationSuggestion:
    """A single optimization opportunity in a prompt."""

    type: str  # "redundancy", "verbosity", "language", "abbreviation", "context"
    original: str
    optimized: str
    tokens_saved: int
    confidence: float = 0.8  # 0.0-1.0


@dataclass
class PromptAnalysis:
    """Analysis results for a prompt."""

    original_text: str
    original_tokens: int
    optimized_text: str
    optimized_tokens: int
    suggestions: list[OptimizationSuggestion] = field(default_factory=list)

    @property
    def savings_percent(self) -> float:
        """Percentage of tokens that could be saved."""
        if self.original_tokens == 0:
            return 0.0
        return (self.original_tokens - self.optimized_tokens) / self.original_tokens * 100

    @property
    def savings_tokens(self) -> int:
        """Absolute number of tokens that could be saved."""
        return self.original_tokens - self.optimized_tokens


class PromptAnalyzer:
    """Analyze and optimize prompts to reduce token usage."""

    # Common verbose phrases and their shorter equivalents
    VERBOSE_REPLACEMENTS = {
        r"\bin order to\b": "to",
        r"\bplease\b": "",
        r"\bthank you\b": "",
        r"\bthank you in advance\b": "",
        r"\bkindly\b": "",
        r"\bI would like you to\b": "",
        r"\bCould you please\b": "Please",
        r"\bWould you be so kind as to\b": "",
        r"\bcould you\b": "can you",
        r"\bwould you\b": "can you",
        r"\bit is necessary that\b": "must",
        r"\bit is important that\b": "must",
        r"\bI think that\b": "",
        r"\bIn my opinion\b": "",
    }

    # Common abbreviations that reduce tokens
    ABBREVIATIONS = {
        r"\butility\b": "util",
        r"\badministration\b": "admin",
        r"\bdocumentation\b": "docs",
        r"\binformation\b": "info",
        r"\bmanagement\b": "mgmt",
        r"\bsignificant\b": "sig",
        r"\bdeveloper\b": "dev",
        r"\bdevelopment\b": "dev",
        r"\bapplication\b": "app",
        r"\barchitecture\b": "arch",
        r"\bconfiguration\b": "config",
    }

    # Turkish → English mapping (English uses ~15-20% fewer tokens)
    TURKISH_KEYWORDS = {
        "lütfen": "please",
        "teşekkür": "thank",
        "önemli": "important",
        "gerekli": "required",
        "işlem": "operation",
        "veri": "data",
        "bilgi": "information",
        "sistem": "system",
        "uygulama": "application",
    }

    def analyze(self, prompt: str, model: str = "claude-3-5-haiku") -> PromptAnalysis:
        """
        Analyze prompt and identify optimization opportunities.

        Args:
            prompt: The prompt to analyze
            model: Model being used (for context)

        Returns:
            PromptAnalysis with original, optimized text and suggestions
        """
        original_tokens = self._estimate_tokens(prompt)
        optimized_text = self._apply_optimizations(prompt, aggressive=False)
        optimized_tokens = self._estimate_tokens(optimized_text)

        suggestions = self._generate_suggestions(prompt, optimized_text)

        return PromptAnalysis(
            original_text=prompt,
            original_tokens=original_tokens,
            optimized_text=optimized_text,
            optimized_tokens=optimized_tokens,
            suggestions=suggestions,
        )

    def optimize(self, prompt: str, aggressive: bool = False) -> str:
        """
        Return optimized version of prompt.

        Args:
            prompt: The prompt to optimize
            aggressive: If True, apply more aggressive optimization

        Returns:
            Optimized prompt text
        """
        return self._apply_optimizations(prompt, aggressive=aggressive)

    def _apply_optimizations(self, prompt: str, aggressive: bool = False) -> str:
        """Apply all optimization strategies to a prompt."""
        text = prompt

        # 1. Remove verbose phrases
        for verbose, replacement in self.VERBOSE_REPLACEMENTS.items():
            text = re.sub(verbose, replacement, text, flags=re.IGNORECASE)

        # 2. Apply abbreviations
        if aggressive:
            for original, abbreviation in self.ABBREVIATIONS.items():
                text = re.sub(original, abbreviation, text, flags=re.IGNORECASE)

        # 3. Remove redundant whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # 4. Aggressive: Remove articles (a, an, the)
        if aggressive:
            text = re.sub(r"\b(a|an|the)\s+", "", text, flags=re.IGNORECASE)

        # 5. Aggressive: Shorten instructions
        if aggressive:
            text = self._shorten_instructions(text)

        return text

    def _shorten_instructions(self, prompt: str) -> str:
        """Shorten verbose instruction blocks."""
        # Detect instruction patterns and compress them
        patterns = [
            (r"Return only the [^.!?]+[.!?]", "Return result only."),
            (r"Do not include [^.!?]+[.!?]", "Skip extras."),
            (r"Make sure to [^.!?]+[.!?]", "Must [extract relevant parts]."),
        ]

        result = prompt
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (simple heuristic: ~4 chars per token)."""
        # Average: 4 characters per token for English
        # Turkish is ~20% less efficient
        return max(1, len(text) // 4)

    def _generate_suggestions(self, original: str, optimized: str) -> list[OptimizationSuggestion]:
        """Generate specific suggestions for optimization."""
        suggestions = []
        original_tokens = self._estimate_tokens(original)
        optimized_tokens = self._estimate_tokens(optimized)

        if original_tokens > optimized_tokens:
            suggestions.append(
                OptimizationSuggestion(
                    type="general_optimization",
                    original=original[:100],
                    optimized=optimized[:100],
                    tokens_saved=original_tokens - optimized_tokens,
                    confidence=0.9,
                )
            )

        # Detect specific optimization opportunities
        if re.search(r"\b(please|kindly|would you|could you)\b", original, re.IGNORECASE):
            suggestions.append(
                OptimizationSuggestion(
                    type="politeness_removal",
                    original="(contains polite phrases)",
                    optimized="(polite phrases removed)",
                    tokens_saved=self._estimate_tokens(original) - self._estimate_tokens(
                        re.sub(r"\b(please|kindly|would you|could you)\b", "", original, flags=re.IGNORECASE)
                    ),
                    confidence=0.8,
                )
            )

        # Detect Turkish content (could be optimized by English translation)
        if self._has_turkish_content(original):
            suggestions.append(
                OptimizationSuggestion(
                    type="language_optimization",
                    original="(Turkish content detected)",
                    optimized="(Use English instead)",
                    tokens_saved=max(1, self._estimate_tokens(original) // 5),  # ~20% savings
                    confidence=0.7,
                )
            )

        return suggestions[:3]  # Return top 3 suggestions

    def _has_turkish_content(self, text: str) -> bool:
        """Check if text contains Turkish-specific characters."""
        turkish_chars = "çğıöşüÇĞİÖŞÜ"
        return any(char in text for char in turkish_chars)

    def suggest_system_prompt(self, task: str) -> str:
        """Suggest an optimized system prompt for a task."""
        suggestions = {
            "clean": "Correct grammar and spelling. Return text only.",
            "summarize": "Summarize in 3 key points. Be concise.",
            "translate": "Translate to English. No explanation.",
            "email": "Draft professional email. Keep it brief.",
            "bullets": "Convert to bullet points. Concise.",
        }
        return suggestions.get(task, "Process text. Return result only.")
