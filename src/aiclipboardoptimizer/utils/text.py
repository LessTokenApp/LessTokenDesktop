"""Text utility helpers."""


def normalize_whitespace(value: str) -> str:
    """Collapse repeated whitespace and trim surrounding spaces."""
    return " ".join(value.split())
