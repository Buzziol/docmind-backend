from dataclasses import dataclass

from app.core.config import settings
from app.models.document_page import DocumentPage


@dataclass(frozen=True)
class GeneratedChunk:
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    token_count: int


@dataclass(frozen=True)
class PageSpan:
    page_number: int
    char_start: int
    char_end: int


def generate_chunks(pages: list[DocumentPage]) -> list[GeneratedChunk]:
    text, page_spans = _build_document_text(pages)
    if not text.strip():
        return []

    chunk_size = settings.CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP
    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be greater than 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be greater than or equal to 0 and smaller than CHUNK_SIZE")

    chunks: list[GeneratedChunk] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        content = text[start:end].strip()
        if content:
            page_start, page_end = _find_page_range(page_spans, start, end)
            chunks.append(
                GeneratedChunk(
                    chunk_index=len(chunks),
                    content=content,
                    page_start=page_start,
                    page_end=page_end,
                    char_start=start,
                    char_end=end,
                    token_count=_estimate_token_count(content),
                )
            )

        if end == len(text):
            break
        start = end - chunk_overlap

    return chunks


def _build_document_text(pages: list[DocumentPage]) -> tuple[str, list[PageSpan]]:
    parts: list[str] = []
    page_spans: list[PageSpan] = []
    cursor = 0

    for page in pages:
        if parts:
            parts.append("\n\n")
            cursor += 2

        page_text = page.text or ""
        start = cursor
        parts.append(page_text)
        cursor += len(page_text)
        page_spans.append(
            PageSpan(
                page_number=page.page_number,
                char_start=start,
                char_end=cursor,
            )
        )

    return "".join(parts), page_spans


def _find_page_range(page_spans: list[PageSpan], char_start: int, char_end: int) -> tuple[int, int]:
    overlapping_pages = [
        page_span.page_number
        for page_span in page_spans
        if page_span.char_start < char_end and page_span.char_end > char_start
    ]

    if not overlapping_pages:
        page_number = page_spans[-1].page_number if page_spans else 1
        return page_number, page_number

    return min(overlapping_pages), max(overlapping_pages)


def _estimate_token_count(content: str) -> int:
    return len(content.split())
