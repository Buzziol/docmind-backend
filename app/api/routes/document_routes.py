import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.document_schema import DocumentListResponse, DocumentResponse
from app.services.document_service import (
    InvalidDocumentUploadError,
    create_document,
    delete_document,
    get_owned_workspace,
    get_user_document,
    list_workspace_documents,
)

router = APIRouter(tags=["documents"])


def get_workspace_or_404(
    db: Session,
    workspace_id: uuid.UUID,
    current_user: User,
) -> Workspace:
    workspace = get_owned_workspace(db, workspace_id, current_user)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return workspace


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_user_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    try:
        return await create_document(db, workspace, file)
    except InvalidDocumentUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=list[DocumentListResponse],
)
def list_documents(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    return list_workspace_documents(db, workspace)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    return get_document_or_404(db, document_id, current_user)


@router.delete("/documents/{document_id}")
def delete(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    document = get_document_or_404(db, document_id, current_user)
    delete_document(db, document)
    return {"message": "Document deleted successfully"}
