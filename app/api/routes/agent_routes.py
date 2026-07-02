import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent_schema import AgentRequest, AgentResponse
from app.services.agent_service import AgentError, run_document_agent, run_workspace_agent
from app.services.analysis_service import AnalysisError
from app.services.document_service import get_user_document
from app.services.llm_service import LlmServiceError
from app.services.rag_service import RagError
from app.services.semantic_search_service import SemanticSearchError
from app.services.workspace_service import get_user_workspace

router = APIRouter(tags=["agent"])


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


def get_workspace_or_404(
    db: Session,
    workspace_id: uuid.UUID,
    current_user: User,
) -> Workspace:
    workspace = get_user_workspace(db, workspace_id, current_user)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


@router.post("/documents/{document_id}/agent", response_model=AgentResponse)
def document_agent(
    document_id: uuid.UUID,
    request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    document = get_document_or_404(db, document_id, current_user)
    try:
        return run_document_agent(db, document, current_user, request)
    except (AgentError, AnalysisError, RagError, SemanticSearchError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/workspaces/{workspace_id}/agent", response_model=AgentResponse)
def workspace_agent(
    workspace_id: uuid.UUID,
    request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    try:
        return run_workspace_agent(db, workspace, current_user, request)
    except (AgentError, RagError, SemanticSearchError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
