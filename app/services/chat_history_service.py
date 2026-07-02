import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage, ChatMessageRole
from app.models.chat_session import ChatSession, ChatSessionScope
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace


def create_document_chat_session(
    db: Session,
    user: User,
    document: Document,
    title: str,
) -> ChatSession:
    session = ChatSession(
        user_id=user.id,
        workspace_id=document.workspace_id,
        document_id=document.id,
        title=_make_title(title),
        scope=ChatSessionScope.DOCUMENT,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_workspace_chat_session(
    db: Session,
    user: User,
    workspace: Workspace,
    title: str,
) -> ChatSession:
    session = ChatSession(
        user_id=user.id,
        workspace_id=workspace.id,
        document_id=None,
        title=_make_title(title),
        scope=ChatSessionScope.WORKSPACE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_user_message(db: Session, session: ChatSession, content: str) -> ChatMessage:
    message = ChatMessage(
        session_id=session.id,
        role=ChatMessageRole.USER,
        content=content,
        sources=None,
        model=None,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def create_assistant_message(
    db: Session,
    session: ChatSession,
    content: str,
    sources: list[dict[str, Any]],
    model: str,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session.id,
        role=ChatMessageRole.ASSISTANT,
        content=content,
        sources=sources,
        model=model,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_document_chat_sessions(
    db: Session,
    user: User,
    document: Document,
) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user.id,
            ChatSession.document_id == document.id,
            ChatSession.scope == ChatSessionScope.DOCUMENT,
        )
        .order_by(ChatSession.created_at.desc())
        .all()
    )


def list_workspace_chat_sessions(
    db: Session,
    user: User,
    workspace: Workspace,
) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user.id,
            ChatSession.workspace_id == workspace.id,
            ChatSession.scope == ChatSessionScope.WORKSPACE,
        )
        .order_by(ChatSession.created_at.desc())
        .all()
    )


def get_user_chat_session(
    db: Session,
    user: User,
    session_id: uuid.UUID,
) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )


def list_chat_messages(db: Session, session: ChatSession) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def delete_chat_session(db: Session, session: ChatSession) -> None:
    db.delete(session)
    db.commit()


def _make_title(question: str) -> str:
    title = " ".join(question.split())
    if len(title) > 80:
        return f"{title[:77]}..."
    return title
