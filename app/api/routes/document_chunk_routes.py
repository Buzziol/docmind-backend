import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.document_chunk_schema import DocumentChunkResponse
from app.services.document_chunk_service import (
    DocumentChunkingError,
    create_document_chunks,
    get_chunkable_document,
    list_document_chunks,
)

router = APIRouter(prefix="/documents", tags=["document chunks"])


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_chunkable_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def create_chunks(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentChunk]:
    document = get_document_or_404(db, document_id, current_user)
    try:
        return create_document_chunks(db, document)
    except DocumentChunkingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def get_chunks(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentChunk]:
    document = get_document_or_404(db, document_id, current_user)
    return list_document_chunks(db, document)
