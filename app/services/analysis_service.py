import uuid
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis_result import AnalysisResult, AnalysisType
from app.models.document import Document
from app.models.user import User
from app.schemas.analysis_schema import AnalysisRequest, AnalysisResponse, AnalysisSource
from app.schemas.semantic_search_schema import SemanticSearchRequest, SemanticSearchResult
from app.services.document_service import get_user_document
from app.services.llm_service import generate_text
from app.services.rag_service import _build_context
from app.services.semantic_search_service import SemanticSearchError, search_document_chunks


class AnalysisError(ValueError):
    pass


ANALYSIS_QUERIES = {
    AnalysisType.EXECUTIVE_SUMMARY: "objetivo partes obrigacoes prazos valores pontos principais",
    AnalysisType.RISK_ANALYSIS: (
        "riscos penalidades multa rescisao responsabilidade obrigacao "
        "confidencialidade prazo pagamento"
    ),
    AnalysisType.DATA_EXTRACTION: (
        "partes datas valores prazos obrigacoes penalidades confidencialidade foro lei aplicavel"
    ),
}


def get_analyzable_document(
    db: Session,
    document_id: uuid.UUID,
    owner: User,
) -> Document | None:
    return get_user_document(db, document_id, owner)


def list_document_analyses(db: Session, document: Document) -> list[AnalysisResult]:
    return (
        db.query(AnalysisResult)
        .filter(AnalysisResult.document_id == document.id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )


def run_document_analysis(
    db: Session,
    document: Document,
    analysis_type: AnalysisType,
    request: AnalysisRequest,
) -> AnalysisResult:
    if not request.force:
        existing = _get_latest_analysis(db, document, analysis_type)
        if existing is not None:
            return existing

    search_response = search_document_chunks(
        db,
        document,
        SemanticSearchRequest(
            query=ANALYSIS_QUERIES[analysis_type],
            top_k=request.top_k,
        ),
    )
    if not search_response.results:
        raise AnalysisError("No embedded chunks found for analysis")

    sources = _sources_from_results(search_response.results)
    prompt = _build_analysis_prompt(analysis_type, sources)
    result = generate_text(prompt)

    analysis = AnalysisResult(
        document_id=document.id,
        analysis_type=analysis_type,
        result=result,
        sources=[source.model_dump(mode="json") for source in sources],
        model=settings.OLLAMA_MODEL,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def to_analysis_response(analysis: AnalysisResult) -> AnalysisResponse:
    return AnalysisResponse(
        id=analysis.id,
        document_id=analysis.document_id,
        analysis_type=analysis.analysis_type,
        result=analysis.result,
        sources=[AnalysisSource(**source) for source in analysis.sources],
        model=analysis.model,
        created_at=analysis.created_at,
    )


def _get_latest_analysis(
    db: Session,
    document: Document,
    analysis_type: AnalysisType,
) -> AnalysisResult | None:
    return (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.document_id == document.id,
            AnalysisResult.analysis_type == analysis_type,
        )
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )


def _sources_from_results(results: Iterable[SemanticSearchResult]) -> list[AnalysisSource]:
    return [
        AnalysisSource(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            document_name=result.document_name,
            chunk_index=result.chunk_index,
            page_start=result.page_start,
            page_end=result.page_end,
            content=result.content,
            score=result.score,
            distance=result.distance,
        )
        for result in results
    ]


def _build_analysis_prompt(analysis_type: AnalysisType, sources: list[AnalysisSource]) -> str:
    context = _build_context(sources)
    instruction = _analysis_instruction(analysis_type)
    return f"""Voce e o DocMind, um copiloto de analise documental empresarial.
Responda em portugues brasileiro.
Use apenas o contexto fornecido.
Nao invente informacoes.
Quando uma informacao nao estiver nas fontes, diga que ela nao foi encontrada.

Contexto:
{context}

Tarefa:
{instruction}

Resposta:"""


def _analysis_instruction(analysis_type: AnalysisType) -> str:
    if analysis_type == AnalysisType.EXECUTIVE_SUMMARY:
        return (
            "Gere um resumo executivo claro em no maximo 5 topicos. "
            "Destaque objetivo do documento, partes envolvidas, obrigacoes principais, "
            "prazos, valores e pontos de atencao quando estiverem nas fontes."
        )

    if analysis_type == AnalysisType.RISK_ANALYSIS:
        return (
            "Identifique riscos contratuais, operacionais, financeiros, juridicos ou de ambiguidade. "
            "Classifique cada risco como BAIXO, MEDIO ou ALTO, explique o motivo e cite pagina/fonte relacionada. "
            "Se nao houver risco claro, diga isso. Nao invente riscos sem base no contexto."
        )

    return (
        "Extraia dados estruturados em JSON textual valido ou proximo de JSON com os campos: "
        "partes_envolvidas, datas_importantes, valores, prazos, obrigacoes, penalidades, "
        "confidencialidade, foro_lei_aplicavel. Use null ou lista vazia quando um campo nao for encontrado."
    )
