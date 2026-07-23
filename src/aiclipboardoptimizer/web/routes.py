"""API routes for Token Optimizer web backend."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from pathlib import Path

from ..ai.processor import AIProcessor, get_operation_labels
from ..config import AppConfig

api_bp = Blueprint("api", __name__)

# Global processor instance (would be per-session in production)
_processor = None


def get_processor():
    """Get or create processor instance."""
    global _processor
    if _processor is None:
        config = AppConfig.from_env()
        _processor = AIProcessor(
            provider=config.ai_provider,
            model=config.provider_models.get(config.ai_provider, "gpt-4o-mini"),
            api_key=config.openai_api_key or config.claude_api_key,
            tracking_enabled=True,
            caching_enabled=True,
            quality_level="balanced",
        )
    return _processor


@api_bp.route("/operations", methods=["GET"])
def get_operations():
    """Get available text operations."""
    labels = get_operation_labels()
    return jsonify({
        "operations": [
            {"key": key, "label": label}
            for key, label in labels.items()
        ]
    })


@api_bp.route("/process", methods=["POST"])
def process_text():
    """Process text with AI or local fallback."""
    try:
        data = request.json
        text = data.get("text", "").strip()
        operation = data.get("operation", "clean")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        processor = get_processor()
        result = processor.optimize_text(text, operation)

        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get token usage statistics."""
    try:
        processor = get_processor()
        period = request.args.get("period", default=30, type=int)

        summary = processor.tracker.get_summary(period_days=period)
        recommendations = processor.tracker.get_recommendations()

        return jsonify({
            "summary": {
                "total_calls": summary["total_calls"],
                "total_tokens": summary["total_input_tokens"] + summary["total_output_tokens"],
                "total_cost": round(summary["total_cost"], 2),
                "by_provider": summary["by_provider"],
                "by_model": summary["by_model"],
                "by_operation": summary["by_operation"],
            },
            "recommendations": [
                {
                    "type": rec.type,
                    "title": rec.title,
                    "description": rec.description,
                    "estimated_savings": round(rec.estimated_savings, 2),
                }
                for rec in recommendations
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/settings", methods=["GET"])
def get_settings():
    """Get current settings."""
    try:
        processor = get_processor()
        return jsonify({
            "provider": processor.provider_name,
            "model": processor.model,
            "quality_level": processor.quality_level,
            "caching_enabled": processor.cache is not None,
            "tracking_enabled": processor.tracker is not None,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/settings", methods=["POST"])
def update_settings():
    """Update settings."""
    try:
        data = request.json
        global _processor

        # Recreate processor with new settings
        provider = data.get("provider", "claude")
        model = data.get("model", "gpt-4o-mini")
        quality_level = data.get("quality_level", "balanced")

        config = AppConfig.from_env()
        api_key = None

        if provider == "openai":
            api_key = config.openai_api_key
        elif provider == "claude":
            api_key = config.claude_api_key
        elif provider == "gemini":
            api_key = config.gemini_api_key

        _processor = AIProcessor(
            provider=provider,
            model=model,
            api_key=api_key,
            tracking_enabled=True,
            caching_enabled=True,
            quality_level=quality_level,
        )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cache-stats", methods=["GET"])
def get_cache_stats():
    """Get cache statistics."""
    try:
        processor = get_processor()
        if processor.cache:
            stats = processor.cache.get_stats()
            return jsonify(stats)
        return jsonify({"error": "Caching not enabled"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
