"""Provider management and coordination service."""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

from .base import BaseService
from ..core.logger import Logger
from ..core.factory import ProviderFactory
from ..ai.providers.base import BaseProvider

logger = Logger.get(__name__)


class SelectionCriteria(str, Enum):
    """Provider selection criteria."""
    CHEAPEST = "cheapest"          # Lowest cost
    FASTEST = "fastest"            # Lowest latency (estimated)
    BALANCED = "balanced"          # Cost-speed tradeoff
    QUALITY = "quality"            # Best quality model
    LOCAL = "local"                # Use local/free provider


@dataclass
class ProviderInfo:
    """Information about a provider."""
    name: str
    provider_instance: BaseProvider
    is_available: bool = True
    is_configured: bool = True
    supported_models: List[str] = field(default_factory=list)
    default_model: str = ""
    estimated_cost_per_1m_tokens: Optional[float] = None
    estimated_latency_ms: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        status = "✓" if self.is_available else "✗"
        return f"{self.name} {status}"


@dataclass
class CostEstimate:
    """Cost estimate for processing."""
    provider_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    estimated_latency_ms: Optional[int] = None

    def __repr__(self) -> str:
        return (
            f"{self.provider_name}/{self.model}: "
            f"${self.total_cost_usd:.6f} (~{self.estimated_latency_ms}ms)"
        )


class ProviderManager(BaseService):
    """Manage and coordinate multiple LLM providers."""

    # Estimated latencies (ms) for different providers
    LATENCY_ESTIMATES = {
        "openai": 500,
        "claude": 800,
        "gemini": 600,
        "ollama": 1000,
        "local": 100,
    }

    def __init__(self, factory: ProviderFactory):
        self.factory = factory
        self._providers: Dict[str, ProviderInfo] = {}
        self._default_provider: Optional[str] = None

    @property
    def service_name(self) -> str:
        return "provider_manager"

    def register_provider(
        self,
        name: str,
        provider: BaseProvider,
        is_default: bool = False,
    ) -> None:
        """Register a provider instance.

        Args:
            name: Provider name (e.g., 'openai', 'claude')
            provider: Provider instance
            is_default: Whether to use as default
        """
        info = ProviderInfo(
            name=name,
            provider_instance=provider,
            is_available=True,
            is_configured=True,
            supported_models=provider.supported_models,
            default_model=provider.supported_models[0] if provider.supported_models else "",
            estimated_latency_ms=self.LATENCY_ESTIMATES.get(name, 500),
        )

        self._providers[name] = info

        if is_default or not self._default_provider:
            self._default_provider = name

        logger.info(f"Registered provider: {name} (default={is_default})")

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get provider instance by name."""
        if name not in self._providers:
            return None

        info = self._providers[name]
        if not info.is_available:
            logger.warning(f"Provider {name} not available")
            return None

        return info.provider_instance

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [
            name for name, info in self._providers.items()
            if info.is_available and info.is_configured
        ]

    def set_default_provider(self, name: str) -> None:
        """Set default provider for processing."""
        if name not in self._providers:
            raise ValueError(f"Provider {name} not found")

        self._default_provider = name
        logger.info(f"Default provider set to: {name}")

    def get_default_provider(self) -> Optional[str]:
        """Get current default provider."""
        return self._default_provider

    def get_provider_info(self, name: str) -> Optional[ProviderInfo]:
        """Get provider information."""
        return self._providers.get(name)

    def list_providers(self) -> List[ProviderInfo]:
        """List all registered providers."""
        return list(self._providers.values())

    def estimate_cost(
        self,
        provider_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Optional[float]:
        """Estimate cost for processing.

        Args:
            provider_name: Provider name
            model: Model identifier
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Estimated cost in USD, or None if cannot estimate
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None

        try:
            return provider.estimate_cost(input_tokens, output_tokens, model)
        except NotImplementedError:
            logger.debug(f"Cost estimation not available for {provider_name}")
            return None

    def compare_providers(
        self,
        input_tokens: int,
        output_tokens: int,
        models: Optional[Dict[str, str]] = None,
    ) -> List[CostEstimate]:
        """Compare costs across providers.

        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            models: Optional {provider_name: model_name} mapping

        Returns:
            List of CostEstimate sorted by cost
        """
        estimates = []

        for provider_name, info in self._providers.items():
            if not info.is_available:
                continue

            # Use specified model or default
            model = (models or {}).get(provider_name, info.default_model)
            if not model:
                continue

            cost = self.estimate_cost(provider_name, model, input_tokens, output_tokens)
            if cost is None:
                continue

            estimate = CostEstimate(
                provider_name=provider_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost_usd=cost,
                estimated_latency_ms=info.estimated_latency_ms,
            )
            estimates.append(estimate)

        # Sort by cost
        estimates.sort(key=lambda e: e.total_cost_usd)
        return estimates

    def select_best_provider(
        self,
        criteria: SelectionCriteria = SelectionCriteria.BALANCED,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> tuple[Optional[str], Optional[str]]:
        """Select best provider based on criteria.

        Args:
            criteria: Selection criteria
            input_tokens: For cost-based selection
            output_tokens: For cost-based selection

        Returns:
            (provider_name, model_name) tuple, or (None, None)
        """
        available = self.get_available_providers()
        if not available:
            logger.warning("No available providers")
            return None, None

        if criteria == SelectionCriteria.LOCAL:
            # Prefer local provider
            if "local" in available:
                info = self._providers["local"]
                return "local", info.default_model
            elif "ollama" in available:
                info = self._providers["ollama"]
                return "ollama", info.default_model
            # Fallback to first available
            info = self._providers[available[0]]
            return available[0], info.default_model

        if criteria == SelectionCriteria.QUALITY:
            # GPT-4o > Claude 3.5 > Gemini > others
            quality_order = ["gpt-4o", "claude", "gemini", "ollama", "local"]
            for pref in quality_order:
                if pref in available:
                    info = self._providers[pref]
                    return pref, info.default_model
            info = self._providers[available[0]]
            return available[0], info.default_model

        if criteria == SelectionCriteria.FASTEST:
            # Sort by latency
            sorted_providers = sorted(
                available,
                key=lambda p: self._providers[p].estimated_latency_ms or 1000,
            )
            info = self._providers[sorted_providers[0]]
            return sorted_providers[0], info.default_model

        if criteria == SelectionCriteria.CHEAPEST:
            # Find cheapest based on token counts
            if input_tokens == 0 and output_tokens == 0:
                # No tokens to estimate, use quality as tiebreaker
                return self.select_best_provider(SelectionCriteria.QUALITY)

            estimates = self.compare_providers(input_tokens, output_tokens)
            if estimates:
                return estimates[0].provider_name, estimates[0].model

            # Fallback
            info = self._providers[available[0]]
            return available[0], info.default_model

        # BALANCED: cost-speed tradeoff
        # Prefer cheap providers with reasonable latency
        for provider_name in sorted(available):
            info = self._providers[provider_name]
            # Skip very slow providers unless necessary
            if info.estimated_latency_ms and info.estimated_latency_ms > 2000:
                continue
            return provider_name, info.default_model

        # Fallback
        info = self._providers[available[0]]
        return available[0], info.default_model

    def on_startup(self) -> None:
        """Initialize provider manager."""
        available = self.get_available_providers()
        logger.info(f"Provider manager started - {len(available)} available providers")
        for name in available:
            logger.debug(f"  ✓ {name}")

    def on_shutdown(self) -> None:
        """Shutdown provider manager."""
        logger.info("Provider manager stopped")
