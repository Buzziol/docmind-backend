import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.document_service import get_user_document
from app.services.embedding_service import generate_embeddings


class DocumentEmbeddingError(ValueError):
    pass


def get_embeddable_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return get_user_document(db, document_id, owner)


def generate_document_embeddings(
    db: Session,
    document: Document,
    reprocess: bool = False,
) -> dict[str, object]:
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    if not chunks:
        raise DocumentEmbeddingError("Document has no chunks to embed")

    chunks_to_embed = [
        chunk
        for chunk in chunks
        if chunk.content.strip() and (reprocess or chunk.embedding is None)
    ]
    if chunks_to_embed:
        embeddings = generate_embeddings([chunk.content for chunk in chunks_to_embed])
        for chunk, embedding in zip(chunks_to_embed, embeddings, strict=True):
            chunk.embedding = embedding
            db.add(chunk)
        db.commit()

    return {
        "document_id": document.id,
        "total_chunks": len(chunks),
        "embedded_chunks": len(chunks_to_embed),
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
    }
