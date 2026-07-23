"""History persistence service with SQLite."""
import sqlite3
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from uuid import uuid4

from .base import BaseService
from .content import ContentType
from ..core.logger import Logger

logger = Logger.get(__name__)


@dataclass
class HistoryEntry:
    """A history entry (transformation result)."""

    id: str
    timestamp: datetime
    original_content: str
    processed_content: str
    content_type: ContentType
    prompt_id: str
    prompt_name: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    metadata: dict

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "original_content": self.original_content,
            "processed_content": self.processed_content,
            "content_type": self.content_type.value,
            "prompt_id": self.prompt_id,
            "prompt_name": self.prompt_name,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "metadata": self.metadata,
        }


class HistoryService(BaseService):
    """Service for persistent history management."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".ai-clipboard-optimizer" / "history.db"
        self._connection: Optional[sqlite3.Connection] = None
        self._setup_database()

    @property
    def service_name(self) -> str:
        return "history"

    def _setup_database(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                original_content TEXT NOT NULL,
                processed_content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                prompt_name TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                metadata TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on timestamp for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp
            ON history(timestamp DESC)
        """)

        # Create index on content_type
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_content_type
            ON history(content_type)
        """)

        # Create index on prompt_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_prompt_id
            ON history(prompt_id)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            # Return rows as dicts
            self._connection.row_factory = sqlite3.Row

        return self._connection

    def add_entry(
        self,
        original_content: str,
        processed_content: str,
        content_type: ContentType,
        prompt_id: str,
        prompt_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        metadata: Optional[dict] = None,
    ) -> str:
        """Add entry to history.

        Returns:
            Entry ID
        """
        entry_id = str(uuid4())
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO history (
                id, timestamp, original_content, processed_content,
                content_type, prompt_id, prompt_name, provider, model,
                input_tokens, output_tokens, cost_usd, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id,
            timestamp,
            original_content,
            processed_content,
            content_type.value,
            prompt_id,
            prompt_name,
            provider,
            model,
            input_tokens,
            output_tokens,
            cost_usd,
            metadata_json,
        ))

        conn.commit()
        logger.debug(f"Added history entry: {entry_id}")

        return entry_id

    def get_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """Get history entry by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM history WHERE id = ?", (entry_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_entry(row)

    def get_recent(self, limit: int = 50) -> List[HistoryEntry]:
        """Get recent history entries."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    def get_by_content_type(self, content_type: ContentType, limit: int = 50) -> List[HistoryEntry]:
        """Get entries by content type."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM history
            WHERE content_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (content_type.value, limit))

        rows = cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    def get_by_prompt(self, prompt_id: str, limit: int = 50) -> List[HistoryEntry]:
        """Get entries by prompt ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM history
            WHERE prompt_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (prompt_id, limit))

        rows = cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    def search(self, query: str, limit: int = 50) -> List[HistoryEntry]:
        """Search history by content (full text search)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        search_query = f"%{query}%"
        cursor.execute("""
            SELECT * FROM history
            WHERE original_content LIKE ? OR processed_content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (search_query, search_query, limit))

        rows = cursor.fetchall()
        return [self._row_to_entry(row) for row in rows]

    def get_statistics(self) -> dict:
        """Get history statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM history")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT SUM(cost_usd) as total_cost FROM history")
        total_cost = cursor.fetchone()["total_cost"] or 0.0

        cursor.execute("SELECT SUM(input_tokens + output_tokens) as total_tokens FROM history")
        total_tokens = cursor.fetchone()["total_tokens"] or 0

        cursor.execute("""
            SELECT content_type, COUNT(*) as count
            FROM history
            GROUP BY content_type
        """)
        content_type_stats = {row["content_type"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT prompt_id, prompt_name, COUNT(*) as count
            FROM history
            GROUP BY prompt_id
            ORDER BY count DESC
            LIMIT 10
        """)
        top_prompts = [
            {"prompt_id": row["prompt_id"], "prompt_name": row["prompt_name"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

        return {
            "total_entries": total,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "content_type_distribution": content_type_stats,
            "top_prompts": top_prompts,
        }

    def clear_history(self, days_old: Optional[int] = None) -> int:
        """Clear history entries.

        Args:
            days_old: If set, only delete entries older than N days

        Returns:
            Number of entries deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if days_old:
            cursor.execute("""
                DELETE FROM history
                WHERE datetime(timestamp) < datetime('now', ? || ' days')
            """, (f"-{days_old}",))
        else:
            cursor.execute("DELETE FROM history")

        conn.commit()
        deleted = cursor.rowcount

        logger.info(f"Deleted {deleted} history entries")
        return deleted

    def _row_to_entry(self, row: sqlite3.Row) -> HistoryEntry:
        """Convert database row to HistoryEntry."""
        return HistoryEntry(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            original_content=row["original_content"],
            processed_content=row["processed_content"],
            content_type=ContentType(row["content_type"]),
            prompt_id=row["prompt_id"],
            prompt_name=row["prompt_name"],
            provider=row["provider"],
            model=row["model"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cost_usd=row["cost_usd"],
            metadata=json.loads(row["metadata"]),
        )

    def on_startup(self) -> None:
        """Initialize history service."""
        stats = self.get_statistics()
        logger.info(
            f"History service started - "
            f"{stats['total_entries']} entries, "
            f"${stats['total_cost_usd']:.2f} spent"
        )

    def on_shutdown(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

        logger.info("History service stopped")
