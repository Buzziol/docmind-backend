import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.analysis_result import AnalysisResult
from app.models.chat_session import ChatSession
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.document_comparison import DocumentComparison
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.dashboard_schema import (
    DashboardDocumentStatusCount,
    DashboardOverviewResponse,
    RecentAnalysisItem,
    RecentChatSessionItem,
    RecentComparisonItem,
    RecentDocumentItem,
    WorkspaceDashboardResponse,
)


def get_dashboard_overview(
    db: Session,
    current_user: User,
    recent_limit: int = 5,
) -> DashboardOverviewResponse:
    workspace_ids_query = db.query(Workspace.id).filter(
        Workspace.owner_id == current_user.id,
    )

    totals = _build_totals(db, workspace_ids_query)

    return DashboardOverviewResponse(
        **totals,
        recent_documents=_list_recent_documents(db, workspace_ids_query, recent_limit),
        recent_analyses=_list_recent_analyses(db, workspace_ids_query, recent_limit),
        recent_comparisons=_list_recent_comparisons(
            db,
            workspace_ids_query,
            recent_limit,
        ),
        recent_chat_sessions=_list_recent_chat_sessions(
            db,
            workspace_ids_query,
            recent_limit,
        ),
    )


def get_workspace_dashboard(
    db: Session,
    workspace_id: uuid.UUID,
    current_user: User,
    recent_limit: int = 5,
) -> WorkspaceDashboardResponse | None:
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.owner_id == current_user.id)
        .first()
    )
    if workspace is None:
        return None

    workspace_ids_query = db.query(Workspace.id).filter(Workspace.id == workspace.id)
    totals = _build_totals(db, workspace_ids_query)

    return WorkspaceDashboardResponse(
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        total_documents=totals["total_documents"],
        documents_by_status=totals["documents_by_status"],
        total_processed_documents=totals["total_processed_documents"],
        total_failed_documents=totals["total_failed_documents"],
        total_uploaded_documents=totals["total_uploaded_documents"],
        total_chunks=totals["total_chunks"],
        total_embedded_chunks=totals["total_embedded_chunks"],
        total_analysis_results=totals["total_analysis_results"],
        total_comparisons=totals["total_comparisons"],
        total_chat_sessions=totals["total_chat_sessions"],
        recent_documents=_list_recent_documents(db, workspace_ids_query, recent_limit),
        recent_analyses=_list_recent_analyses(db, workspace_ids_query, recent_limit),
        recent_comparisons=_list_recent_comparisons(
            db,
            workspace_ids_query,
            recent_limit,
        ),
        recent_chat_sessions=_list_recent_chat_sessions(
            db,
            workspace_ids_query,
            recent_limit,
        ),
    )


def _build_totals(db: Session, workspace_ids_query) -> dict:
    documents_by_status = _count_documents_by_status(db, workspace_ids_query)
    status_counts = {item.status: item.count for item in documents_by_status}

    return {
        "total_workspaces": _count_workspaces(db, workspace_ids_query),
        "total_documents": _count_documents(db, workspace_ids_query),
        "documents_by_status": documents_by_status,
        "total_processed_documents": status_counts.get(DocumentStatus.PROCESSED, 0),
        "total_failed_documents": status_counts.get(DocumentStatus.FAILED, 0),
        "total_uploaded_documents": status_counts.get(DocumentStatus.UPLOADED, 0),
        "total_chunks": _count_chunks(db, workspace_ids_query),
        "total_embedded_chunks": _count_embedded_chunks(db, workspace_ids_query),
        "total_analysis_results": _count_analysis_results(db, workspace_ids_query),
        "total_comparisons": _count_comparisons(db, workspace_ids_query),
        "total_chat_sessions": _count_chat_sessions(db, workspace_ids_query),
    }


def _scalar_count(query) -> int:
    return int(query.scalar() or 0)


def _count_workspaces(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(Workspace.id)).filter(Workspace.id.in_(workspace_ids_query)),
    )


def _count_documents(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(Document.id)).filter(
            Document.workspace_id.in_(workspace_ids_query),
        ),
    )


def _count_documents_by_status(
    db: Session,
    workspace_ids_query,
) -> list[DashboardDocumentStatusCount]:
    rows = (
        db.query(Document.status, func.count(Document.id))
        .filter(Document.workspace_id.in_(workspace_ids_query))
        .group_by(Document.status)
        .order_by(Document.status)
        .all()
    )
    return [
        DashboardDocumentStatusCount(status=status, count=int(count or 0))
        for status, count in rows
    ]


def _count_chunks(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(DocumentChunk.id))
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.workspace_id.in_(workspace_ids_query)),
    )


def _count_embedded_chunks(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(DocumentChunk.id))
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(
            Document.workspace_id.in_(workspace_ids_query),
            DocumentChunk.embedding.is_not(None),
        ),
    )


def _count_analysis_results(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(AnalysisResult.id))
        .join(Document, Document.id == AnalysisResult.document_id)
        .filter(Document.workspace_id.in_(workspace_ids_query)),
    )


def _count_comparisons(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(DocumentComparison.id)).filter(
            DocumentComparison.workspace_id.in_(workspace_ids_query),
        ),
    )


def _count_chat_sessions(db: Session, workspace_ids_query) -> int:
    return _scalar_count(
        db.query(func.count(ChatSession.id)).filter(
            ChatSession.workspace_id.in_(workspace_ids_query),
        ),
    )


def _list_recent_documents(
    db: Session,
    workspace_ids_query,
    recent_limit: int,
) -> list[RecentDocumentItem]:
    rows = (
        db.query(Document, Workspace.name.label("workspace_name"))
        .join(Workspace, Workspace.id == Document.workspace_id)
        .filter(Document.workspace_id.in_(workspace_ids_query))
        .order_by(Document.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    return [
        RecentDocumentItem(
            id=document.id,
            workspace_id=document.workspace_id,
            workspace_name=workspace_name,
            original_filename=document.original_filename,
            status=document.status,
            total_pages=document.total_pages,
            created_at=document.created_at,
            processed_at=document.processed_at,
        )
        for document, workspace_name in rows
    ]


def _list_recent_analyses(
    db: Session,
    workspace_ids_query,
    recent_limit: int,
) -> list[RecentAnalysisItem]:
    rows = (
        db.query(AnalysisResult, Document.original_filename.label("document_name"))
        .join(Document, Document.id == AnalysisResult.document_id)
        .filter(Document.workspace_id.in_(workspace_ids_query))
        .order_by(AnalysisResult.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    return [
        RecentAnalysisItem(
            id=analysis.id,
            document_id=analysis.document_id,
            document_name=document_name,
            analysis_type=analysis.analysis_type,
            created_at=analysis.created_at,
        )
        for analysis, document_name in rows
    ]


def _list_recent_comparisons(
    db: Session,
    workspace_ids_query,
    recent_limit: int,
) -> list[RecentComparisonItem]:
    base_document = aliased(Document)
    target_document = aliased(Document)
    rows = (
        db.query(
            DocumentComparison,
            Workspace.name.label("workspace_name"),
            base_document.original_filename.label("base_document_name"),
            target_document.original_filename.label("target_document_name"),
        )
        .join(Workspace, Workspace.id == DocumentComparison.workspace_id)
        .join(base_document, base_document.id == DocumentComparison.base_document_id)
        .join(
            target_document,
            target_document.id == DocumentComparison.target_document_id,
        )
        .filter(DocumentComparison.workspace_id.in_(workspace_ids_query))
        .order_by(DocumentComparison.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    return [
        RecentComparisonItem(
            id=comparison.id,
            workspace_id=comparison.workspace_id,
            workspace_name=workspace_name,
            base_document_id=comparison.base_document_id,
            base_document_name=base_document_name,
            target_document_id=comparison.target_document_id,
            target_document_name=target_document_name,
            comparison_type=comparison.comparison_type,
            created_at=comparison.created_at,
        )
        for comparison, workspace_name, base_document_name, target_document_name in rows
    ]


def _list_recent_chat_sessions(
    db: Session,
    workspace_ids_query,
    recent_limit: int,
) -> list[RecentChatSessionItem]:
    rows = (
        db.query(
            ChatSession,
            Workspace.name.label("workspace_name"),
            Document.original_filename.label("document_name"),
        )
        .join(Workspace, Workspace.id == ChatSession.workspace_id)
        .outerjoin(Document, Document.id == ChatSession.document_id)
        .filter(ChatSession.workspace_id.in_(workspace_ids_query))
        .order_by(ChatSession.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    return [
        RecentChatSessionItem(
            id=session.id,
            workspace_id=session.workspace_id,
            workspace_name=workspace_name,
            document_id=session.document_id,
            document_name=document_name,
            title=session.title,
            scope=session.scope,
            created_at=session.created_at,
        )
        for session, workspace_name, document_name in rows
    ]
