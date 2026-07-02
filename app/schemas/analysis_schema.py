import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.analysis_result import AnalysisType


class AnalysisRequest(BaseModel):
    force: bool = False
    top_k: int = Field(default=8, ge=1, le=15)


class AnalysisSource(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    page_start: int
    page_end: int
    content: str
    score: float
    distance: float


class AnalysisResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    analysis_type: AnalysisType
    result: str
    sources: list[AnalysisSource]
    model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
