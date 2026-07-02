import uuid

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_page import DocumentPage
from app.models.user import User
from app.services.chunking_service import generate_chunks
from app.services.document_service import get_user_document


class DocumentChunkingError(ValueError):
    pass


def get_chunkable_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return get_user_document(db, document_id, owner)


def list_document_chunks(
    db: Session,
    document: Document,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def create_document_chunks(
    db: Session,
    document: Document,
) -> list[DocumentChunk]:
    if document.status != DocumentStatus.PROCESSED:
        raise DocumentChunkingError("Document must be PROCESSED before generating chunks")

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document.id)
        .order_by(DocumentPage.page_number.asc())
        .all()
    )
    if not pages:
        raise DocumentChunkingError("Document has no extracted pages")

    generated_chunks = generate_chunks(pages)
    if not generated_chunks:
        raise DocumentChunkingError("Document has no text content to generate chunks")

    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete(
        synchronize_session=False
    )
    db.flush()

    chunks: list[DocumentChunk] = []
    for generated_chunk in generated_chunks:
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=generated_chunk.chunk_index,
            content=generated_chunk.content,
            page_start=generated_chunk.page_start,
            page_end=generated_chunk.page_end,
            char_start=generated_chunk.char_start,
            char_end=generated_chunk.char_end,
            token_count=generated_chunk.token_count,
        )
        db.add(chunk)
        chunks.append(chunk)

    db.commit()
    for chunk in chunks:
        db.refresh(chunk)

    return list_document_chunks(db, document)
