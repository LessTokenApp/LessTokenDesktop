"""File processing service for PDFs, Word docs, and other formats."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import json

from .base import BaseService
from .content import ContentType
from ..core.logger import Logger

logger = Logger.get(__name__)


@dataclass
class FileExtractionResult:
    """Result of file text extraction."""
    file_path: Path
    file_type: str
    total_pages: Optional[int] = None
    total_chars: int = 0
    total_words: int = 0
    extracted_text: str = ""
    pages_extracted: List[int] = field(default_factory=list)
    token_estimate: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def text_summary(self) -> str:
        """Short summary of extracted text."""
        words = self.extracted_text.split()
        return " ".join(words[:50]) + ("..." if len(words) > 50 else "")


class FileService(BaseService):
    """Service for processing files (PDF, Word, etc.)."""

    # Token estimation: ~1 token per 4 characters (average)
    CHARS_PER_TOKEN = 4

    # Supported formats
    SUPPORTED_FORMATS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json"}

    def __init__(self):
        self._pdf_available = self._check_pdf_support()
        self._docx_available = self._check_docx_support()

    @property
    def service_name(self) -> str:
        return "file"

    @staticmethod
    def _pdf_reader_class():
        """Return a PdfReader class, or None when no PDF library is installed.

        pypdf is the maintained successor to PyPDF2 and is what
        requirements.txt installs; PyPDF2 is accepted for older environments.
        Both expose the same PdfReader API.
        """
        try:
            from pypdf import PdfReader
            return PdfReader
        except ImportError:
            pass
        try:
            from PyPDF2 import PdfReader
            return PdfReader
        except ImportError:
            return None

    def _check_pdf_support(self) -> bool:
        """Check if PDF support available."""
        if self._pdf_reader_class() is not None:
            logger.info("PDF support available")
            return True
        logger.warning("PDF support not available - install pypdf")
        return False

    def _check_docx_support(self) -> bool:
        """Check if Word support available."""
        try:
            from docx import Document
            logger.info("Word document support available")
            return True
        except ImportError:
            logger.warning("Word support not available - install python-docx")
            return False

    def extract(
        self,
        file_path: Path,
        pages: Optional[List[int]] = None,
    ) -> FileExtractionResult:
        """Extract text from file.

        Args:
            file_path: Path to file
            pages: For PDFs, specific pages to extract (1-indexed)

        Returns:
            FileExtractionResult with extracted text and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format not supported
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {suffix}")

        logger.info(f"Extracting text from: {file_path.name}")

        if suffix == ".pdf":
            return self._extract_pdf(file_path, pages)
        elif suffix in {".docx", ".doc"}:
            return self._extract_docx(file_path)
        elif suffix == ".txt":
            return self._extract_txt(file_path)
        elif suffix == ".md":
            return self._extract_markdown(file_path)
        elif suffix == ".csv":
            return self._extract_csv(file_path)
        elif suffix == ".json":
            return self._extract_json(file_path)
        else:
            raise ValueError(f"Format not implemented: {suffix}")

    def _extract_pdf(self, file_path: Path, pages: Optional[List[int]] = None) -> FileExtractionResult:
        """Extract text from PDF."""
        if not self._pdf_available:
            raise RuntimeError("PDF support not available")

        try:
            pdf_reader_class = self._pdf_reader_class()

            with open(file_path, "rb") as f:
                reader = pdf_reader_class(f)
                total_pages = len(reader.pages)

                # Determine which pages to extract
                page_indices = []
                if pages:
                    # Convert 1-indexed to 0-indexed
                    page_indices = [p - 1 for p in pages if 1 <= p <= total_pages]
                else:
                    page_indices = list(range(total_pages))

                # Extract text
                extracted_text = ""
                for idx in page_indices:
                    page = reader.pages[idx]
                    extracted_text += page.extract_text() + "\n"

            extracted_text = extracted_text.strip()
            total_chars = len(extracted_text)
            total_words = len(extracted_text.split())
            token_estimate = total_chars // self.CHARS_PER_TOKEN

            logger.info(
                f"PDF extracted: {len(page_indices)} pages, "
                f"{total_chars:,} chars, ~{token_estimate:,} tokens"
            )

            return FileExtractionResult(
                file_path=file_path,
                file_type="pdf",
                total_pages=total_pages,
                total_chars=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                pages_extracted=page_indices,
                token_estimate=token_estimate,
                metadata={"pages_extracted": len(page_indices)},
            )

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

    def _extract_docx(self, file_path: Path) -> FileExtractionResult:
        """Extract text from Word document."""
        if not self._docx_available:
            raise RuntimeError("Word support not available")

        try:
            from docx import Document

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted_text = "\n".join(paragraphs)

            total_chars = len(extracted_text)
            total_words = len(extracted_text.split())
            token_estimate = total_chars // self.CHARS_PER_TOKEN

            logger.info(
                f"Word document extracted: {len(paragraphs)} paragraphs, "
                f"{total_chars:,} chars, ~{token_estimate:,} tokens"
            )

            return FileExtractionResult(
                file_path=file_path,
                file_type="word",
                total_chars=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                token_estimate=token_estimate,
                metadata={"paragraphs": len(paragraphs)},
            )

        except Exception as e:
            logger.error(f"Word extraction failed: {e}")
            raise

    def _extract_txt(self, file_path: Path) -> FileExtractionResult:
        """Extract text from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                extracted_text = f.read()

            total_chars = len(extracted_text)
            total_words = len(extracted_text.split())
            token_estimate = total_chars // self.CHARS_PER_TOKEN

            logger.info(f"Text file extracted: {total_chars:,} chars, ~{token_estimate:,} tokens")

            return FileExtractionResult(
                file_path=file_path,
                file_type="text",
                total_chars=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                token_estimate=token_estimate,
            )

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise

    def _extract_markdown(self, file_path: Path) -> FileExtractionResult:
        """Extract text from Markdown file."""
        # Same as plain text for now
        return self._extract_txt(file_path)

    def _extract_csv(self, file_path: Path) -> FileExtractionResult:
        """Extract text from CSV file."""
        try:
            import csv

            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Format as text
            extracted_text = "\n".join([",".join(row) for row in rows])

            total_chars = len(extracted_text)
            total_words = len(extracted_text.split())
            token_estimate = total_chars // self.CHARS_PER_TOKEN

            logger.info(f"CSV extracted: {len(rows)} rows, ~{token_estimate:,} tokens")

            return FileExtractionResult(
                file_path=file_path,
                file_type="csv",
                total_chars=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                token_estimate=token_estimate,
                metadata={"rows": len(rows)},
            )

        except Exception as e:
            logger.error(f"CSV extraction failed: {e}")
            raise

    def _extract_json(self, file_path: Path) -> FileExtractionResult:
        """Extract and format JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Pretty print JSON
            extracted_text = json.dumps(data, indent=2)

            total_chars = len(extracted_text)
            total_words = len(extracted_text.split())
            token_estimate = total_chars // self.CHARS_PER_TOKEN

            logger.info(f"JSON extracted: {total_chars:,} chars, ~{token_estimate:,} tokens")

            return FileExtractionResult(
                file_path=file_path,
                file_type="json",
                total_chars=total_chars,
                total_words=total_words,
                extracted_text=extracted_text,
                token_estimate=token_estimate,
            )

        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            raise

    def batch_extract(
        self,
        file_dir: Path,
        pattern: str = "*",
    ) -> List[FileExtractionResult]:
        """Extract text from multiple files.

        Args:
            file_dir: Directory containing files
            pattern: File pattern to match (e.g., "*.pdf")

        Returns:
            List of extraction results
        """
        file_dir = Path(file_dir)
        results = []

        for file_path in file_dir.glob(pattern):
            if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                continue

            try:
                result = self.extract(file_path)
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to extract {file_path}: {e}")

        logger.info(f"Batch extraction complete: {len(results)} files")
        return results

    def get_file_info(self, file_path: Path) -> dict:
        """Get file information."""
        file_path = Path(file_path)
        size_mb = file_path.stat().st_size / (1024 * 1024)

        return {
            "path": str(file_path),
            "name": file_path.name,
            "format": file_path.suffix,
            "size_mb": round(size_mb, 2),
            "supported": file_path.suffix.lower() in self.SUPPORTED_FORMATS,
        }

    def on_startup(self) -> None:
        """Initialize file service."""
        pdf_status = "✓" if self._pdf_available else "✗"
        docx_status = "✓" if self._docx_available else "✗"
        logger.info(f"File service started - PDF {pdf_status}, Word {docx_status}")

    def on_shutdown(self) -> None:
        """Shutdown file service."""
        logger.info("File service stopped")
