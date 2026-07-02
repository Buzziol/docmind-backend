import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    total_pages: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(DocumentResponse):
    pass


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: DocumentStatus
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
