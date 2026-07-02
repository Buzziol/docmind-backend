import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.analysis_result import AnalysisType
from app.models.chat_session import ChatSessionScope
from app.models.document import DocumentStatus
from app.models.document_comparison import DocumentComparisonType


class DashboardDocumentStatusCount(BaseModel):
    status: DocumentStatus
    count: int


class RecentDocumentItem(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    workspace_name: str
    original_filename: str
    status: DocumentStatus
    total_pages: int
    created_at: datetime
    processed_at: datetime | None


class RecentAnalysisItem(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    analysis_type: AnalysisType
    created_at: datetime


class RecentComparisonItem(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    workspace_name: str
    base_document_id: uuid.UUID
    base_document_name: str
    target_document_id: uuid.UUID
    target_document_name: str
    comparison_type: DocumentComparisonType
    created_at: datetime


class RecentChatSessionItem(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    workspace_name: str
    document_id: uuid.UUID | None
    document_name: str | None
    title: str
    scope: ChatSessionScope
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    total_workspaces: int
    total_documents: int
    documents_by_status: list[DashboardDocumentStatusCount]
    total_processed_documents: int
    total_failed_documents: int
    total_uploaded_documents: int
    total_chunks: int
    total_embedded_chunks: int
    total_analysis_results: int
    total_comparisons: int
    total_chat_sessions: int
    recent_documents: list[RecentDocumentItem]
    recent_analyses: list[RecentAnalysisItem]
    recent_comparisons: list[RecentComparisonItem]
    recent_chat_sessions: list[RecentChatSessionItem]


class WorkspaceDashboardResponse(BaseModel):
    workspace_id: uuid.UUID
    workspace_name: str
    total_documents: int
    documents_by_status: list[DashboardDocumentStatusCount]
    total_processed_documents: int
    total_failed_documents: int
    total_uploaded_documents: int
    total_chunks: int
    total_embedded_chunks: int
    total_analysis_results: int
    total_comparisons: int
    total_chat_sessions: int
    recent_documents: list[RecentDocumentItem]
    recent_analyses: list[RecentAnalysisItem]
    recent_comparisons: list[RecentComparisonItem]
    recent_chat_sessions: list[RecentChatSessionItem]
