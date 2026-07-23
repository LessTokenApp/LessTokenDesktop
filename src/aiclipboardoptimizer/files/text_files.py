"""Helpers for loading and saving user files."""
from pathlib import Path

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".py", ".js", ".ts",
    ".html", ".css", ".xml", ".yaml", ".yml", ".log",
}


def load_text_from_file(path: str | Path) -> str:
    """Load readable text from a supported file."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        return file_path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        return _load_pdf(file_path)
    if suffix == ".docx":
        return _load_docx(file_path)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def save_text_to_file(path: str | Path, text: str) -> Path:
    """Save text to a UTF-8 file and return the path."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(text, encoding="utf-8")
    return file_path


def _load_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ValueError("PDF okumak icin pypdf paketi kurulu olmali.") from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page for page in pages if page.strip())


def _load_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ValueError("Word dosyasi okumak icin python-docx paketi kurulu olmali.") from exc

    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
