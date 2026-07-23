"""Prompt result caching to reduce API calls."""
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class CachedResult:
    """A cached API response."""

    prompt_hash: str
    prompt_text: str
    result_text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str  # ISO format datetime
    ttl_hours: int = 24

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        cached_time = datetime.fromisoformat(self.timestamp)
        expiry_time = cached_time + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry_time


class PromptCache:
    """File-based prompt result cache with TTL support."""

    def __init__(self, cache_dir: Path = None, ttl_hours: int = 24) -> None:
        """Initialize cache with directory and TTL."""
        if cache_dir is None:
            cache_dir = Path(__file__).resolve().parents[2] / "outputs" / "prompt_cache"

        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, prompt: str, provider: str, model: str) -> Optional[CachedResult]:
        """
        Retrieve cached result if available and not expired.

        Args:
            prompt: The prompt text
            provider: Provider name
            model: Model identifier

        Returns:
            CachedResult if found and fresh, None otherwise
        """
        cache_key = self._get_cache_key(prompt, provider, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = CachedResult(**data)

            # Check expiration
            if result.is_expired:
                cache_file.unlink()  # Delete expired cache
                return None

            return result
        except (json.JSONDecodeError, ValueError, KeyError):
            # Corrupted cache file
            cache_file.unlink()
            return None

    def set(self, prompt: str, result_text: str, provider: str, model: str,
            input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        """
        Store result in cache.

        Args:
            prompt: The prompt that was sent
            result_text: The result from the API
            provider: Provider name
            model: Model identifier
            input_tokens: Tokens used for input
            output_tokens: Tokens in output
            cost_usd: Cost of the API call
        """
        cache_key = self._get_cache_key(prompt, provider, model)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cached_result = CachedResult(
            prompt_hash=cache_key,
            prompt_text=prompt,
            result_text=result_text,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            timestamp=datetime.now().isoformat(),
            ttl_hours=self.ttl_hours,
        )

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(asdict(cached_result), f, indent=2)
        except IOError:
            pass  # Silent fail - cache is optional

    def invalidate(self, older_than_hours: int = 24) -> int:
        """
        Delete cache entries older than N hours.

        Args:
            older_than_hours: Delete entries older than this many hours

        Returns:
            Number of cache files deleted
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                timestamp = datetime.fromisoformat(data["timestamp"])
                if timestamp < cutoff_time:
                    cache_file.unlink()
                    deleted_count += 1
            except (json.JSONDecodeError, ValueError, KeyError):
                # Delete corrupted files
                cache_file.unlink()
                deleted_count += 1

        return deleted_count

    def clear(self) -> int:
        """Delete all cache files. Returns count of deleted files."""
        deleted_count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                deleted_count += 1
            except OSError:
                pass
        return deleted_count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files) / 1024  # KB

        # Count hits vs total entries
        expired_count = 0
        valid_count = 0

        for cache_file in cache_files:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                result = CachedResult(**data)
                if result.is_expired:
                    expired_count += 1
                else:
                    valid_count += 1
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        return {
            "total_entries": len(cache_files),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "total_size_kb": round(total_size, 2),
        }

    @staticmethod
    def _get_cache_key(prompt: str, provider: str, model: str) -> str:
        """Generate cache key from prompt, provider, and model."""
        # Normalize prompt (lowercase, strip whitespace)
        normalized = prompt.lower().strip()
        # Create composite key with provider and model
        composite = f"{normalized}:{provider}:{model}"
        # Hash it
        return hashlib.sha256(composite.encode()).hexdigest()[:16]


class SemanticCache:
    """Advanced caching with semantic similarity matching (future enhancement)."""

    def __init__(self, cache_dir: Path = None) -> None:
        """Initialize semantic cache."""
        if cache_dir is None:
            cache_dir = Path(__file__).resolve().parents[2] / "outputs" / "semantic_cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings = {}  # In-memory cache of embeddings

    def find_similar(self, prompt: str, threshold: float = 0.95) -> list[CachedResult]:
        """
        Find semantically similar cached prompts (stub for future).

        Args:
            prompt: Query prompt
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of similar cached results

        Note:
            This is a placeholder. Full implementation would require:
            - Sentence transformer embeddings
            - Vector similarity search
            - Approximate nearest neighbor indexing
        """
        # TODO: Implement semantic search with embeddings
        # For now, return empty list
        return []
