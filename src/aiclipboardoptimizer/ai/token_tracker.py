"""Token usage tracking and cost analysis."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class TokenUsage:
    """Record of a single API call with token and cost information."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime
    operation: str
    source_length: int  # Length of input text before prompt construction


@dataclass
class Recommendation:
    """Cost optimization recommendation."""

    type: str  # "switch_model", "use_cache", "batch_process"
    title: str
    description: str
    estimated_savings: float  # Dollars saved per month
    confidence: float  # 0.0-1.0


class TokenTracker:
    """Track token usage and provide cost analytics."""

    def __init__(self, db_path: Path = None) -> None:
        """Initialize token tracker with SQLite database."""
        if db_path is None:
            db_path = Path(__file__).resolve().parents[2] / "outputs" / "token_usage.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create SQLite database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    source_length INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON token_usage(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider ON token_usage(provider)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON token_usage(model)
            """)
            conn.commit()

    def track(self, usage: TokenUsage) -> None:
        """Record a token usage event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO token_usage (
                    provider, model, input_tokens, output_tokens, cost_usd, timestamp, operation, source_length
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.provider,
                usage.model,
                usage.input_tokens,
                usage.output_tokens,
                usage.cost_usd,
                usage.timestamp.isoformat(),
                usage.operation,
                usage.source_length,
            ))
            conn.commit()

    def get_summary(self, period_days: int = 30) -> dict:
        """Get usage summary for the last N days."""
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Total stats
            total_row = conn.execute("""
                SELECT
                    COUNT(*) as calls,
                    SUM(input_tokens) as input_tokens,
                    SUM(output_tokens) as output_tokens,
                    SUM(cost_usd) as total_cost
                FROM token_usage
                WHERE timestamp >= ?
            """, (cutoff_date,)).fetchone()

            # By provider
            by_provider = conn.execute("""
                SELECT provider, COUNT(*) as calls, SUM(cost_usd) as cost
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY provider
                ORDER BY cost DESC
            """, (cutoff_date,)).fetchall()

            # By model
            by_model = conn.execute("""
                SELECT model, COUNT(*) as calls, SUM(cost_usd) as cost
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY cost DESC
            """, (cutoff_date,)).fetchall()

            # By operation
            by_operation = conn.execute("""
                SELECT operation, COUNT(*) as calls, SUM(cost_usd) as cost
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY operation
                ORDER BY cost DESC
            """, (cutoff_date,)).fetchall()

        return {
            "period_days": period_days,
            "total_calls": total_row[0] or 0,
            "total_input_tokens": total_row[1] or 0,
            "total_output_tokens": total_row[2] or 0,
            "total_cost": total_row[3] or 0.0,
            "by_provider": [{"provider": row[0], "calls": row[1], "cost": row[2]} for row in by_provider],
            "by_model": [{"model": row[0], "calls": row[1], "cost": row[2]} for row in by_model],
            "by_operation": [{"operation": row[0], "calls": row[1], "cost": row[2]} for row in by_operation],
        }

    def get_recommendations(self) -> list[Recommendation]:
        """Generate cost optimization recommendations based on usage patterns."""
        summary = self.get_summary(period_days=30)
        recommendations = []

        # Recommendation 1: If using expensive models frequently
        by_model = summary["by_model"]
        if by_model:
            expensive_model = by_model[0]
            if expensive_model["cost"] > 10.0:  # > $10 per month on single model
                recommendations.append(
                    Recommendation(
                        type="switch_model",
                        title=f"Consider cheaper model instead of {expensive_model['model']}",
                        description=f"Your most expensive model costs ${expensive_model['cost']:.2f}/month. "
                        "Try Claude Haiku (80% cheaper) for simple tasks.",
                        estimated_savings=expensive_model["cost"] * 0.75,
                        confidence=0.8,
                    )
                )

        # Recommendation 2: If making many small API calls
        if summary["total_calls"] > 100:
            recommendations.append(
                Recommendation(
                    type="batch_process",
                    title="Consider batching API calls",
                    description=f"You're making {summary['total_calls']} API calls. "
                    "Processing in batches could save 20-30% on overhead.",
                    estimated_savings=summary["total_cost"] * 0.25,
                    confidence=0.7,
                )
            )

        # Recommendation 3: If very low input/output ratio (lots of setup overhead)
        if summary["total_input_tokens"] > 0:
            ratio = summary["total_output_tokens"] / summary["total_input_tokens"]
            if ratio < 0.2:  # Output is <20% of input (lots of prompt overhead)
                recommendations.append(
                    Recommendation(
                        type="prompt_optimization",
                        title="Optimize prompts to reduce input tokens",
                        description="Your input tokens are high relative to output. "
                        "Try shorter, more focused prompts to save 15-30%.",
                        estimated_savings=summary["total_cost"] * 0.20,
                        confidence=0.75,
                    )
                )

        return sorted(recommendations, key=lambda r: r.estimated_savings, reverse=True)

    def get_daily_breakdown(self, period_days: int = 30) -> dict:
        """Get day-by-day cost breakdown."""
        cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            daily = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as calls,
                    SUM(input_tokens) as input_tokens,
                    SUM(output_tokens) as output_tokens,
                    SUM(cost_usd) as cost
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (cutoff_date,)).fetchall()

        return {
            "dates": [
                {
                    "date": row[0],
                    "calls": row[1],
                    "input_tokens": row[2],
                    "output_tokens": row[3],
                    "cost": row[4],
                }
                for row in daily
            ]
        }

    def clear_old_records(self, older_than_days: int = 90) -> int:
        """Delete records older than N days. Returns count of deleted records."""
        cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM token_usage WHERE timestamp < ?
            """, (cutoff_date,))
            conn.commit()
            return cursor.rowcount
