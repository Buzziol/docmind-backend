import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document_embedding_schema import DocumentEmbeddingResponse
from app.services.document_embedding_service import (
    DocumentEmbeddingError,
    generate_document_embeddings,
    get_embeddable_document,
)

router = APIRouter(prefix="/documents", tags=["document embeddings"])


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_embeddable_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post("/{document_id}/embeddings", response_model=DocumentEmbeddingResponse)
def create_embeddings(
    document_id: uuid.UUID,
    reprocess: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    document = get_document_or_404(db, document_id, current_user)
    try:
        return generate_document_embeddings(db, document, reprocess=reprocess)
    except DocumentEmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
