import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document_comparison import DocumentComparison
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.document_comparison_schema import (
    DocumentComparisonListResponse,
    DocumentComparisonRequest,
    DocumentComparisonResponse,
)
from app.services.document_comparison_service import (
    DocumentComparisonError,
    create_or_get_document_comparison,
    delete_document_comparison,
    get_comparison_workspace,
    get_user_comparison,
    list_workspace_comparisons,
    to_document_comparison_response,
)
from app.services.llm_service import LlmServiceError

router = APIRouter(tags=["document comparisons"])


def get_workspace_or_404(
    db: Session,
    workspace_id: uuid.UUID,
    current_user: User,
) -> Workspace:
    workspace = get_comparison_workspace(db, workspace_id, current_user)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


def get_comparison_or_404(
    db: Session,
    comparison_id: uuid.UUID,
    current_user: User,
) -> DocumentComparison:
    comparison = get_user_comparison(db, comparison_id, current_user)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document comparison not found",
        )
    return comparison


@router.post(
    "/workspaces/{workspace_id}/comparisons",
    response_model=DocumentComparisonResponse,
)
def create_comparison(
    workspace_id: uuid.UUID,
    request: DocumentComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentComparisonResponse:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    try:
        comparison = create_or_get_document_comparison(db, workspace, request)
        return to_document_comparison_response(comparison)
    except DocumentComparisonError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "Document not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get(
    "/workspaces/{workspace_id}/comparisons",
    response_model=list[DocumentComparisonListResponse],
)
def list_comparisons(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentComparisonResponse]:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    return [
        to_document_comparison_response(comparison)
        for comparison in list_workspace_comparisons(db, workspace)
    ]


@router.get("/comparisons/{comparison_id}", response_model=DocumentComparisonResponse)
def get_comparison(
    comparison_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentComparisonResponse:
    comparison = get_comparison_or_404(db, comparison_id, current_user)
    return to_document_comparison_response(comparison)


@router.delete("/comparisons/{comparison_id}")
def delete_comparison(
    comparison_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    comparison = get_comparison_or_404(db, comparison_id, current_user)
    delete_document_comparison(db, comparison)
    return {"message": "Document comparison deleted successfully"}
