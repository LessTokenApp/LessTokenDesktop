"""Application configuration."""
from dataclasses import dataclass, field
from pathlib import Path
import os

PREFIX = "AI_CLIPBOARD_OPTIMIZER_"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    """Configuration loaded from environment variables."""

    app_name: str = "Less Token"
    poll_interval_seconds: float = 1.0
    ai_provider: str = "local"
    ai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"
    output_dir: Path = PROJECT_ROOT / "outputs"
    # API keys for different providers
    openai_api_key: str | None = None
    claude_api_key: str | None = None
    gemini_api_key: str | None = None
    # Model configuration per provider
    provider_models: dict[str, str] = field(
        default_factory=lambda: {
            "openai": "gpt-4o-mini",
            "claude": "claude-3-5-haiku-20241022",
            "gemini": "gemini-2.5-flash",
            "ollama": "mistral",
            "local": "regex",
        }
    )

    @classmethod
    def from_env(cls) -> "AppConfig":
        output_dir = Path(os.getenv(f"{PREFIX}OUTPUT_DIR", PROJECT_ROOT / "outputs"))

        # Parse provider models from env if set
        provider_models_dict = {
            "openai": os.getenv(f"{PREFIX}MODEL_OPENAI", "gpt-4o-mini"),
            "claude": os.getenv(f"{PREFIX}MODEL_CLAUDE", "claude-3-5-haiku-20241022"),
            "gemini": os.getenv(f"{PREFIX}MODEL_GEMINI", "gemini-2.5-flash"),
            "ollama": os.getenv(f"{PREFIX}MODEL_OLLAMA", "mistral"),
            "local": os.getenv(f"{PREFIX}MODEL_LOCAL", "regex"),
        }

        return cls(
            poll_interval_seconds=_env_float("POLL_INTERVAL", 1.0),
            ai_provider=os.getenv(f"{PREFIX}AI_PROVIDER", "local"),
            ai_model=os.getenv(f"{PREFIX}AI_MODEL", "gpt-4o-mini"),
            log_level=os.getenv(f"{PREFIX}LOG_LEVEL", "INFO"),
            output_dir=output_dir,
            openai_api_key=os.getenv(f"{PREFIX}OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            claude_api_key=os.getenv(f"{PREFIX}CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
            gemini_api_key=os.getenv(f"{PREFIX}GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            provider_models=provider_models_dict,
        )


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(f"{PREFIX}{name}")
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default
