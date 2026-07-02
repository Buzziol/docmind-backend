import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.rag_schema import RagAnswerResponse, RagQuestionRequest
from app.services.chat_history_service import (
    create_assistant_message,
    create_document_chat_session,
    create_user_message,
    create_workspace_chat_session,
)
from app.services.llm_service import LlmServiceError
from app.services.rag_service import RagError, answer_document_question, answer_workspace_question
from app.services.semantic_search_service import (
    SemanticSearchError,
    get_searchable_document,
    get_searchable_workspace,
)

router = APIRouter(tags=["rag"])


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


@router.post("/documents/{document_id}/ask", response_model=RagAnswerResponse)
def ask_document(
    document_id: uuid.UUID,
    question_request: RagQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagAnswerResponse:
    document = get_document_or_404(db, document_id, current_user)
    try:
        response = answer_document_question(db, document, question_request)
        session = create_document_chat_session(db, current_user, document, question_request.question)
        create_user_message(db, session, question_request.question)
        create_assistant_message(
            db,
            session,
            response.answer,
            [source.model_dump(mode="json") for source in response.sources],
            response.model,
        )
        response.chat_session_id = session.id
        return response
    except SemanticSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No embedded chunks found for RAG",
        ) from exc
    except RagError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/workspaces/{workspace_id}/ask", response_model=RagAnswerResponse)
def ask_workspace(
    workspace_id: uuid.UUID,
    question_request: RagQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagAnswerResponse:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    try:
        response = answer_workspace_question(db, workspace, question_request)
        session = create_workspace_chat_session(db, current_user, workspace, question_request.question)
        create_user_message(db, session, question_request.question)
        create_assistant_message(
            db,
            session,
            response.answer,
            [source.model_dump(mode="json") for source in response.sources],
            response.model,
        )
        response.chat_session_id = session.id
        return response
    except SemanticSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No embedded chunks found for RAG",
        ) from exc
    except RagError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
