"""Prompt management service."""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
import json
from pathlib import Path

from .base import BaseService
from .content import ContentType
from ..core.logger import Logger

logger = Logger.get(__name__)


@dataclass
class Prompt:
    """A reusable prompt template."""

    id: str
    name: str
    description: str
    content: str
    category: str = "general"
    content_types: List[ContentType] = field(default_factory=lambda: [ContentType.TEXT])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "content_types": [ct.value for ct in self.content_types],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """Create from dictionary."""
        data = data.copy()
        data["content_types"] = [ContentType(ct) for ct in data.get("content_types", ["text"])]
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


class PromptService(BaseService):
    """Service for managing prompts."""

    # Built-in prompts
    BUILTIN_PROMPTS = {
        "fix-grammar": Prompt(
            id="fix-grammar",
            name="Fix Grammar",
            description="Fix grammar and spelling errors",
            content="Fix the grammar and spelling in the following text, maintaining the original meaning:\n\n{text}",
            category="text",
            content_types=[ContentType.TEXT, ContentType.EMAIL],
        ),
        "summarize": Prompt(
            id="summarize",
            name="Summarize",
            description="Create a concise summary",
            content="Summarize the following text in 2-3 sentences:\n\n{text}",
            category="text",
        ),
        "expand": Prompt(
            id="expand",
            name="Expand",
            description="Expand with more details",
            content="Expand the following text with more details and examples:\n\n{text}",
            category="text",
        ),
        "code-review": Prompt(
            id="code-review",
            name="Code Review",
            description="Review code for issues and improvements",
            content="Review the following code. Identify potential bugs, performance issues, and suggest improvements:\n\n{text}",
            category="code",
            content_types=[ContentType.CODE],
        ),
        "explain-code": Prompt(
            id="explain-code",
            name="Explain Code",
            description="Explain what code does",
            content="Explain what the following code does in simple terms:\n\n{text}",
            category="code",
            content_types=[ContentType.CODE],
        ),
        "json-format": Prompt(
            id="json-format",
            name="Format JSON",
            description="Pretty-print and validate JSON",
            content="Format the following JSON with proper indentation and validate it:\n\n{text}",
            category="json",
            content_types=[ContentType.JSON],
        ),
        "markdown-format": Prompt(
            id="markdown-format",
            name="Format Markdown",
            description="Clean up and improve Markdown formatting",
            content="Improve the formatting and structure of the following Markdown:\n\n{text}",
            category="markdown",
            content_types=[ContentType.MARKDOWN],
        ),
    }

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir
        self._prompts: Dict[str, Prompt] = {}

        # Load built-in prompts
        self._prompts.update(self.BUILTIN_PROMPTS)

        # Load from file if available
        if prompts_dir:
            self._load_prompts()

    @property
    def service_name(self) -> str:
        return "prompt"

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get prompt by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Prompt or None if not found
        """
        return self._prompts.get(prompt_id)

    def get_all_prompts(self) -> List[Prompt]:
        """Get all prompts."""
        return list(self._prompts.values())

    def get_prompts_for_content_type(self, content_type: ContentType) -> List[Prompt]:
        """Get prompts suitable for content type.

        Args:
            content_type: Type of content

        Returns:
            List of applicable prompts
        """
        return [
            p for p in self._prompts.values()
            if content_type in p.content_types or ContentType.TEXT in p.content_types
        ]

    def get_prompts_by_category(self, category: str) -> List[Prompt]:
        """Get prompts by category."""
        return [p for p in self._prompts.values() if p.category == category]

    def create_prompt(self, prompt: Prompt) -> None:
        """Create custom prompt.

        Args:
            prompt: Prompt to create
        """
        if prompt.id in self._prompts:
            logger.warning(f"Prompt {prompt.id} already exists, overwriting")

        self._prompts[prompt.id] = prompt
        logger.info(f"Created prompt: {prompt.name}")

        # Save to file if directory is set
        if self.prompts_dir:
            self._save_prompts()

    def update_prompt(self, prompt_id: str, **kwargs) -> None:
        """Update prompt fields.

        Args:
            prompt_id: Prompt to update
            **kwargs: Fields to update
        """
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")

        prompt = self._prompts[prompt_id]
        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        prompt.updated_at = datetime.now()
        logger.info(f"Updated prompt: {prompt.name}")

        if self.prompts_dir:
            self._save_prompts()

    def increment_usage(self, prompt_id: str) -> None:
        """Increment usage counter for prompt."""
        if prompt_id in self._prompts:
            self._prompts[prompt_id].usage_count += 1

    def delete_prompt(self, prompt_id: str) -> None:
        """Delete custom prompt (built-ins cannot be deleted)."""
        if prompt_id in self.BUILTIN_PROMPTS:
            raise ValueError("Cannot delete built-in prompts")

        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            logger.info(f"Deleted prompt: {prompt_id}")

            if self.prompts_dir:
                self._save_prompts()

    def get_popular_prompts(self, limit: int = 5) -> List[Prompt]:
        """Get most frequently used prompts."""
        sorted_prompts = sorted(
            self._prompts.values(),
            key=lambda p: p.usage_count,
            reverse=True,
        )
        return sorted_prompts[:limit]

    def _load_prompts(self) -> None:
        """Load prompts from file."""
        if not self.prompts_dir:
            return

        prompts_file = self.prompts_dir / "prompts.json"
        if not prompts_file.exists():
            return

        try:
            with open(prompts_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for prompt_data in data.get("custom_prompts", []):
                prompt = Prompt.from_dict(prompt_data)
                self._prompts[prompt.id] = prompt

            logger.info(f"Loaded {len(data.get('custom_prompts', []))} custom prompts")

        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")

    def _save_prompts(self) -> None:
        """Save prompts to file."""
        if not self.prompts_dir:
            return

        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        prompts_file = self.prompts_dir / "prompts.json"

        try:
            # Only save custom prompts (not built-ins)
            custom_prompts = [
                p.to_dict()
                for p in self._prompts.values()
                if p.id not in self.BUILTIN_PROMPTS
            ]

            data = {"custom_prompts": custom_prompts}

            with open(prompts_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(custom_prompts)} custom prompts")

        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")

    def on_startup(self) -> None:
        """Initialize prompt service."""
        logger.info(f"Prompt service started with {len(self._prompts)} prompts")

    def on_shutdown(self) -> None:
        """Shutdown prompt service."""
        logger.info("Prompt service stopped")
