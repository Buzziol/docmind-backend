import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.analysis_result import AnalysisResult, AnalysisType
from app.models.document import Document
from app.models.user import User
from app.schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import (
    AnalysisError,
    get_analyzable_document,
    list_document_analyses,
    run_document_analysis,
    to_analysis_response,
)
from app.services.llm_service import LlmServiceError
from app.services.semantic_search_service import SemanticSearchError

router = APIRouter(prefix="/documents", tags=["document analysis"])


def get_document_or_404(
    db: Session,
    document_id: uuid.UUID,
    current_user: User,
) -> Document:
    document = get_analyzable_document(db, document_id, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


def _run_analysis_endpoint(
    db: Session,
    document: Document,
    analysis_type: AnalysisType,
    request: AnalysisRequest,
) -> AnalysisResponse:
    try:
        analysis = run_document_analysis(db, document, analysis_type, request)
        return to_analysis_response(analysis)
    except SemanticSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No embedded chunks found for analysis",
        ) from exc
    except AnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LlmServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/{document_id}/analysis/summary", response_model=AnalysisResponse)
def executive_summary(
    document_id: uuid.UUID,
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    document = get_document_or_404(db, document_id, current_user)
    return _run_analysis_endpoint(db, document, AnalysisType.EXECUTIVE_SUMMARY, request)


@router.post("/{document_id}/analysis/risks", response_model=AnalysisResponse)
def risk_analysis(
    document_id: uuid.UUID,
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    document = get_document_or_404(db, document_id, current_user)
    return _run_analysis_endpoint(db, document, AnalysisType.RISK_ANALYSIS, request)


@router.post("/{document_id}/analysis/extract", response_model=AnalysisResponse)
def data_extraction(
    document_id: uuid.UUID,
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    document = get_document_or_404(db, document_id, current_user)
    return _run_analysis_endpoint(db, document, AnalysisType.DATA_EXTRACTION, request)


@router.get("/{document_id}/analysis", response_model=list[AnalysisResponse])
def list_analyses(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalysisResponse]:
    document = get_document_or_404(db, document_id, current_user)
    analyses: list[AnalysisResult] = list_document_analyses(db, document)
    return [to_analysis_response(analysis) for analysis in analyses]
