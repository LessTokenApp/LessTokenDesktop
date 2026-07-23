"""Content detection and type identification service."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import mimetypes

from .base import BaseService
from ..core.logger import Logger

logger = Logger.get(__name__)


class ContentType(str, Enum):
    """Supported content types."""
    TEXT = "text"
    CODE = "code"
    EMAIL = "email"
    URL = "url"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    IMAGE = "image"
    FILE = "file"
    UNKNOWN = "unknown"


@dataclass
class ContentInfo:
    """Information about detected content."""
    content_type: ContentType
    content: str
    language: Optional[str] = None
    confidence: float = 1.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContentDetector(BaseService):
    """Service for detecting content type and characteristics."""

    def __init__(self):
        self._language_keywords = {
            "python": ["def ", "import ", "class ", "if __name__"],
            "javascript": ["function ", "const ", "let ", "import {", "=>"],
            "java": ["public class ", "public static void", "import java"],
            "go": ["func ", "package main", "defer ", "go "],
            "rust": ["fn ", "let ", "mut ", "impl ", "struct "],
            "sql": ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", "WHERE "],
            "bash": ["#!/bin/bash", "#!/bin/sh", "echo ", "export ", "if [ "],
        }

    @property
    def service_name(self) -> str:
        return "content_detector"

    def detect(self, content: str) -> ContentInfo:
        """Detect content type from string.

        Args:
            content: Content to analyze

        Returns:
            ContentInfo with detected type and metadata
        """
        if not content or not isinstance(content, str):
            return ContentInfo(content_type=ContentType.UNKNOWN, content=content)

        content = content.strip()

        # Check for email
        if self._is_email(content):
            return ContentInfo(
                content_type=ContentType.EMAIL,
                content=content,
                confidence=0.9,
            )

        # Check for URL
        if self._is_url(content):
            return ContentInfo(
                content_type=ContentType.URL,
                content=content,
                confidence=0.95,
            )

        # Check for JSON
        if self._is_json(content):
            return ContentInfo(
                content_type=ContentType.JSON,
                content=content,
                confidence=0.95,
            )

        # Check for YAML
        if self._is_yaml(content):
            return ContentInfo(
                content_type=ContentType.YAML,
                content=content,
                confidence=0.8,
            )

        # Check for Markdown
        if self._is_markdown(content):
            return ContentInfo(
                content_type=ContentType.MARKDOWN,
                content=content,
                confidence=0.75,
            )

        # Check for code
        language = self._detect_code_language(content)
        if language:
            return ContentInfo(
                content_type=ContentType.CODE,
                content=content,
                language=language,
                confidence=0.85,
            )

        # Default to plain text
        return ContentInfo(
            content_type=ContentType.TEXT,
            content=content,
            confidence=1.0,
        )

    def _is_email(self, content: str) -> bool:
        """Check if content is email address."""
        return "@" in content and "." in content and len(content) < 100 and "\n" not in content

    def _is_url(self, content: str) -> bool:
        """Check if content is URL."""
        return (content.startswith("http://") or content.startswith("https://")) and "\n" not in content

    def _is_json(self, content: str) -> bool:
        """Check if content is JSON."""
        try:
            import json
            json.loads(content)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def _is_yaml(self, content: str) -> bool:
        """Check if content looks like YAML."""
        lines = content.split("\n")
        yaml_indicators = 0

        for line in lines[:10]:  # Check first 10 lines
            if line.startswith("-") or ":" in line and not line.startswith("#"):
                yaml_indicators += 1

        return yaml_indicators > 2

    def _is_markdown(self, content: str) -> bool:
        """Check if content is Markdown."""
        markdown_patterns = [
            content.startswith("#"),  # Headers
            "**" in content or "__" in content,  # Bold
            "*" in content or "_" in content,  # Italic
            "[" in content and "](" in content,  # Links
            "```" in content,  # Code blocks
        ]
        return sum(markdown_patterns) >= 2

    def _detect_code_language(self, content: str) -> Optional[str]:
        """Detect programming language from code snippet."""
        lines = content.split("\n")
        first_lines = "\n".join(lines[:10])

        best_match = None
        best_score = 0

        for language, keywords in self._language_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in first_lines.lower())

            if score > best_score:
                best_score = score
                best_match = language

        return best_match if best_score >= 2 else None
