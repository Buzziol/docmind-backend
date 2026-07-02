import uuid

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class RagQuestionRequest(BaseModel):
    question: str
    top_k: int = Field(default=settings.RAG_TOP_K, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Question cannot be empty")
        return normalized


class RagSource(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    page_start: int
    page_end: int
    content: str
    score: float
    distance: float


class RagAnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]
    model: str
    total_sources: int
    chat_session_id: uuid.UUID | None = None
