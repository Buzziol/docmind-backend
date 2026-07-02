import uuid

from pydantic import BaseModel, Field, field_validator


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float | None = None
    document_id: uuid.UUID | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Query cannot be empty")
        return normalized


class SemanticSearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    score: float
    distance: float


class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SemanticSearchResult]
