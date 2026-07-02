import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.rag_schema import RagSource


class AgentIntent(str, Enum):
    RAG_QA = "RAG_QA"
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    DATA_EXTRACTION = "DATA_EXTRACTION"


class AgentRequest(BaseModel):
    message: str
    top_k: int = Field(default=5, ge=1, le=15)
    force: bool = False

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Message cannot be empty")
        return normalized


class AgentDecision(BaseModel):
    intent: AgentIntent
    confidence: float = Field(ge=0, le=1)
    reason: str


class AgentResponse(BaseModel):
    input: str
    decision: AgentDecision
    result_type: str
    result: Any
    sources: list[RagSource] | None = None
    chat_session_id: uuid.UUID | None = None
    analysis_id: uuid.UUID | None = None
    model: str | None = None
