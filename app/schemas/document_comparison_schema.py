import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.document_comparison import DocumentComparisonType


class DocumentRole(str, Enum):
    BASE = "BASE"
    TARGET = "TARGET"


class DocumentComparisonRequest(BaseModel):
    base_document_id: uuid.UUID
    target_document_id: uuid.UUID
    comparison_type: DocumentComparisonType = DocumentComparisonType.GENERAL
    force: bool = False
    top_k: int = Field(default=8, ge=1, le=15)

    @model_validator(mode="after")
    def validate_documents(self):
        if self.base_document_id == self.target_document_id:
            raise ValueError("base_document_id and target_document_id must be different")
        return self


class DocumentComparisonSource(BaseModel):
    document_role: DocumentRole
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    page_start: int
    page_end: int
    content: str
    score: float | None = None
    distance: float | None = None


class DocumentComparisonResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    base_document_id: uuid.UUID
    target_document_id: uuid.UUID
    comparison_type: DocumentComparisonType
    result: str
    sources: list[DocumentComparisonSource]
    model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentComparisonListResponse(DocumentComparisonResponse):
    pass
