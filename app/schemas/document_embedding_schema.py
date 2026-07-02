import uuid

from pydantic import BaseModel


class DocumentEmbeddingResponse(BaseModel):
    document_id: uuid.UUID
    total_chunks: int
    embedded_chunks: int
    embedding_model: str
    embedding_dimension: int
