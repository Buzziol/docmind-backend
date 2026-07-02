import uuid
from typing import NamedTuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.semantic_search_schema import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from app.services.document_service import get_user_document
from app.services.embedding_service import generate_embedding
from app.services.workspace_service import get_user_workspace


class SemanticSearchError(ValueError):
    pass


class SearchScope(NamedTuple):
    document: Document | None = None
    workspace: Workspace | None = None


def get_searchable_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return get_user_document(db, document_id, owner)


def get_searchable_workspace(
    db: Session,
    workspace_id: uuid.UUID,
    owner: User,
) -> Workspace | None:
    return get_user_workspace(db, workspace_id, owner)


def search_document_chunks(
    db: Session,
    document: Document,
    search_request: SemanticSearchRequest,
) -> SemanticSearchResponse:
    return _search_chunks(
        db=db,
        search_request=search_request,
        scope=SearchScope(document=document),
    )


def search_workspace_chunks(
    db: Session,
    workspace: Workspace,
    search_request: SemanticSearchRequest,
) -> SemanticSearchResponse:
    return _search_chunks(
        db=db,
        search_request=search_request,
        scope=SearchScope(workspace=workspace),
    )


def _search_chunks(
    db: Session,
    search_request: SemanticSearchRequest,
    scope: SearchScope,
) -> SemanticSearchResponse:
    query_embedding = generate_embedding(search_request.query)
    distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

    query = (
        db.query(DocumentChunk, Document.original_filename, distance_expr)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.embedding.is_not(None))
    )

    if scope.document is not None:
        query = query.filter(DocumentChunk.document_id == scope.document.id)

    if scope.workspace is not None:
        query = query.filter(Document.workspace_id == scope.workspace.id)
        if search_request.document_id is not None:
            query = query.filter(Document.id == search_request.document_id)

    embedded_count = query.with_entities(func.count(DocumentChunk.id)).scalar() or 0
    if embedded_count == 0:
        raise SemanticSearchError("No embedded chunks found for semantic search")

    rows = query.order_by(distance_expr.asc()).limit(search_request.top_k).all()

    results: list[SemanticSearchResult] = []
    for chunk, document_name, distance in rows:
        distance_value = float(distance)
        score = 1.0 - distance_value
        if search_request.min_score is not None and score < search_request.min_score:
            continue

        results.append(
            SemanticSearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=document_name,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                score=score,
                distance=distance_value,
            )
        )

    return SemanticSearchResponse(
        query=search_request.query,
        total_results=len(results),
        results=results,
    )
