import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.chat_session import ChatSession
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.chat_schema import ChatHistoryResponse, ChatSessionResponse
from app.services.chat_history_service import (
    delete_chat_session,
    get_user_chat_session,
    list_chat_messages,
    list_document_chat_sessions,
    list_workspace_chat_sessions,
)
from app.services.document_service import get_user_document
from app.services.workspace_service import get_user_workspace

router = APIRouter(tags=["chat history"])


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


def get_session_or_404(
    db: Session,
    session_id: uuid.UUID,
    current_user: User,
) -> ChatSession:
    session = get_user_chat_session(db, current_user, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return session


@router.get(
    "/documents/{document_id}/chat-sessions",
    response_model=list[ChatSessionResponse],
)
def list_document_sessions(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSession]:
    document = get_document_or_404(db, document_id, current_user)
    return list_document_chat_sessions(db, current_user, document)


@router.get(
    "/workspaces/{workspace_id}/chat-sessions",
    response_model=list[ChatSessionResponse],
)
def list_workspace_sessions(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSession]:
    workspace = get_workspace_or_404(db, workspace_id, current_user)
    return list_workspace_chat_sessions(db, current_user, workspace)


@router.get("/chat-sessions/{session_id}", response_model=ChatHistoryResponse)
def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    session = get_session_or_404(db, session_id, current_user)
    messages = list_chat_messages(db, session)
    return ChatHistoryResponse(session=session, messages=messages)


@router.delete("/chat-sessions/{session_id}")
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    session = get_session_or_404(db, session_id, current_user)
    delete_chat_session(db, session)
    return {"message": "Chat session deleted successfully"}
