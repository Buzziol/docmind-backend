from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ExtractedPdfPage(TypedDict):
    page_number: int
    text: str


class PdfProcessingError(RuntimeError):
    pass


def extract_pdf_pages(file_path: str) -> list[ExtractedPdfPage]:
    path = Path(file_path)
    if not path.exists():
        raise PdfProcessingError("PDF file was not found")

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise PdfProcessingError("PDF file is encrypted and cannot be read") from exc

        pages: list[ExtractedPdfPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page_number": index, "text": text.strip()})

        return pages
    except PdfProcessingError:
        raise
    except (OSError, PdfReadError, ValueError) as exc:
        raise PdfProcessingError("PDF file could not be read") from exc
