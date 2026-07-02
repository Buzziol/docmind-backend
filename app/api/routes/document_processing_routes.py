import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.user import User
from app.schemas.document_page_schema import DocumentPageResponse
from app.schemas.document_schema import DocumentResponse
from app.services.document_processing_service import (
    DocumentProcessingError,
    get_processable_document,
    list_document_pages,
    process_document,
)

router = APIRouter(prefix="/documents", tags=["document processing"])


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_processable_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    document = get_document_or_404(db, document_id, current_user)
    try:
        return process_document(db, document)
    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{document_id}/pages", response_model=list[DocumentPageResponse])
def pages(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentPage]:
    document = get_document_or_404(db, document_id, current_user)
    return list_document_pages(db, document)
