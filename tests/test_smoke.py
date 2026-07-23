"""Smoke tests for the app."""

from aiclipboardoptimizer.ai.processor import AIProcessor, get_operation_labels


def test_processor_returns_cleaned_text() -> None:
    processor = AIProcessor()

    result = processor.optimize_text("  hello   clipboard  ", "clean")

    assert result == "hello clipboard"


def test_processor_can_make_bullets() -> None:
    processor = AIProcessor()

    result = processor.optimize_text("one. two.", "bullets")

    assert "- one." in result
    assert "- two." in result


def test_operation_labels_are_available() -> None:
    labels = get_operation_labels()

    assert "clean" in labels
    assert "translate_en" in labels

    result = processor.optimize_text("one. two.", "bullets")

    assert "- one." in result
    assert "- two." in result


def test_operation_labels_are_available() -> None:
    labels = get_operation_labels()

    assert "clean" in labels
    assert "translate_en" in labels
