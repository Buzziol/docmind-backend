import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.semantic_search_schema import (
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.semantic_search_service import (
    SemanticSearchError,
    get_searchable_document,
    get_searchable_workspace,
    search_document_chunks,
    search_workspace_chunks,
)

router = APIRouter(tags=["semantic search"])


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_searchable_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


def get_workspace_or_404(
    db: Session,
    workspace_id: uuid.UUID,
    current_user: User,
) -> Workspace:
    workspace = get_searchable_workspace(db, workspace_id, current_user)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


@router.post(
    "/documents/{document_id}/semantic-search",
    response_model=SemanticSearchResponse,
)
def search_document(
    document_id: uuid.UUID,
    search_request: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticSearchResponse:
    document = get_document_or_404(db, document_id, current_user)
    try:
        return search_document_chunks(db, document, search_request)
    except SemanticSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/workspaces/{workspace_id}/semantic-search",
    response_model=SemanticSearchResponse,
)
def search_workspace(
    workspace_id: uuid.UUID,
    search_request: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticSearchResponse:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    try:
        return search_workspace_chunks(db, workspace, search_request)
    except SemanticSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
