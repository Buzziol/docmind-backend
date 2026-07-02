import uuid
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_comparison import DocumentComparison, DocumentComparisonType
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.document_comparison_schema import (
    DocumentComparisonRequest,
    DocumentComparisonResponse,
    DocumentComparisonSource,
    DocumentRole,
)
from app.schemas.semantic_search_schema import SemanticSearchRequest, SemanticSearchResult
from app.services.llm_service import generate_text
from app.services.semantic_search_service import SemanticSearchError, search_document_chunks
from app.services.workspace_service import get_user_workspace


class DocumentComparisonError(ValueError):
    pass


COMPARISON_QUERIES = {
    DocumentComparisonType.GENERAL: (
        "principais diferencas alteracoes clausulas obrigacoes valores prazos riscos "
        "penalidades confidencialidade"
    ),
    DocumentComparisonType.RISKS: (
        "riscos penalidades multas responsabilidade rescisao descumprimento obrigacao "
        "sensivel clausula problematica"
    ),
    DocumentComparisonType.FINANCIAL: (
        "valores pagamento preco multa reajuste vencimento obrigacao financeira cobranca taxa"
    ),
    DocumentComparisonType.DATES: (
        "datas prazos vigencia vencimento inicio termino renovacao prazo de pagamento"
    ),
    DocumentComparisonType.OBLIGATIONS: (
        "obrigacoes responsabilidades deveres contratante contratada entrega prestacao servico obrigacao"
    ),
}


def get_comparison_workspace(
    db: Session,
    workspace_id: uuid.UUID,
    owner: User,
) -> Workspace | None:
    return get_user_workspace(db, workspace_id, owner)


def get_user_comparison(
    db: Session,
    comparison_id: uuid.UUID,
    owner: User,
) -> DocumentComparison | None:
    return (
        db.query(DocumentComparison)
        .join(Workspace, DocumentComparison.workspace_id == Workspace.id)
        .filter(DocumentComparison.id == comparison_id, Workspace.owner_id == owner.id)
        .first()
    )


def list_workspace_comparisons(
    db: Session,
    workspace: Workspace,
) -> list[DocumentComparison]:
    return (
        db.query(DocumentComparison)
        .filter(DocumentComparison.workspace_id == workspace.id)
        .order_by(DocumentComparison.created_at.desc())
        .all()
    )


def create_or_get_document_comparison(
    db: Session,
    workspace: Workspace,
    request: DocumentComparisonRequest,
) -> DocumentComparison:
    base_document = _get_document_in_workspace(db, workspace, request.base_document_id)
    target_document = _get_document_in_workspace(db, workspace, request.target_document_id)
    if base_document is None or target_document is None:
        raise DocumentComparisonError("Document not found")

    if not request.force:
        existing = _get_latest_comparison(db, workspace, request)
        if existing is not None:
            return existing

    query = COMPARISON_QUERIES[request.comparison_type]
    try:
        base_results = search_document_chunks(
            db,
            base_document,
            SemanticSearchRequest(query=query, top_k=request.top_k),
        ).results
        target_results = search_document_chunks(
            db,
            target_document,
            SemanticSearchRequest(query=query, top_k=request.top_k),
        ).results
    except SemanticSearchError as exc:
        raise DocumentComparisonError(
            "Both documents must have embedded chunks before comparison"
        ) from exc

    if not base_results or not target_results:
        raise DocumentComparisonError("Both documents must have embedded chunks before comparison")

    sources = [
        *_sources_from_results(DocumentRole.BASE, base_results),
        *_sources_from_results(DocumentRole.TARGET, target_results),
    ]
    prompt = _build_comparison_prompt(request.comparison_type, sources)
    result = generate_text(prompt)

    comparison = DocumentComparison(
        workspace_id=workspace.id,
        base_document_id=base_document.id,
        target_document_id=target_document.id,
        comparison_type=request.comparison_type,
        result=result,
        sources=[source.model_dump(mode="json") for source in sources],
        model=settings.OLLAMA_MODEL,
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison


def delete_document_comparison(db: Session, comparison: DocumentComparison) -> None:
    db.delete(comparison)
    db.commit()


def to_document_comparison_response(
    comparison: DocumentComparison,
) -> DocumentComparisonResponse:
    return DocumentComparisonResponse(
        id=comparison.id,
        workspace_id=comparison.workspace_id,
        base_document_id=comparison.base_document_id,
        target_document_id=comparison.target_document_id,
        comparison_type=comparison.comparison_type,
        result=comparison.result,
        sources=[DocumentComparisonSource(**source) for source in comparison.sources],
        model=comparison.model,
        created_at=comparison.created_at,
    )


def _get_document_in_workspace(
    db: Session,
    workspace: Workspace,
    document_id: uuid.UUID,
) -> Document | None:
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.workspace_id == workspace.id)
        .first()
    )


def _get_latest_comparison(
    db: Session,
    workspace: Workspace,
    request: DocumentComparisonRequest,
) -> DocumentComparison | None:
    return (
        db.query(DocumentComparison)
        .filter(
            DocumentComparison.workspace_id == workspace.id,
            DocumentComparison.base_document_id == request.base_document_id,
            DocumentComparison.target_document_id == request.target_document_id,
            DocumentComparison.comparison_type == request.comparison_type,
        )
        .order_by(DocumentComparison.created_at.desc())
        .first()
    )


def _sources_from_results(
    role: DocumentRole,
    results: Iterable[SemanticSearchResult],
) -> list[DocumentComparisonSource]:
    return [
        DocumentComparisonSource(
            document_role=role,
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


def _build_comparison_prompt(
    comparison_type: DocumentComparisonType,
    sources: list[DocumentComparisonSource],
) -> str:
    context = _build_context_for_comparison(sources)
    instruction = _comparison_instruction(comparison_type)
    return f"""Voce e o DocMind, um copiloto de analise documental empresarial.
Compare apenas com base no contexto fornecido.
Nao invente mudancas.
Quando a evidencia for insuficiente, diga isso claramente.
Use Documento Base e Documento Alvo como referencias.
Responda em portugues brasileiro, de forma estruturada.

Contexto:
{context}

Tarefa:
{instruction}

Resposta:"""


def _build_context_for_comparison(sources: list[DocumentComparisonSource]) -> str:
    blocks = []
    current_size = 0
    for source in sources:
        label = "Documento Base" if source.document_role == DocumentRole.BASE else "Documento Alvo"
        block = (
            f"{label}\n"
            f"Arquivo: {source.document_name}\n"
            f"Paginas: {source.page_start}-{source.page_end}\n"
            f"Chunk: {source.chunk_index}\n"
            f"Conteudo:\n{source.content}\n"
        )
        remaining = settings.RAG_MAX_CONTEXT_CHARS - current_size
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining]
        blocks.append(block)
        current_size += len(block)

    return "\n---\n".join(blocks)


def _comparison_instruction(comparison_type: DocumentComparisonType) -> str:
    if comparison_type == DocumentComparisonType.RISKS:
        return (
            "Compare mudancas que aumentam ou reduzem risco. Classifique diferencas como "
            "BAIXO, MEDIO ou ALTO quando possivel, explique o motivo e cite fontes dos dois documentos."
        )
    if comparison_type == DocumentComparisonType.FINANCIAL:
        return (
            "Compare valores, pagamentos, multas, reajustes e obrigacoes financeiras. "
            "Destaque mudancas numericas e informe quando valores nao forem encontrados."
        )
    if comparison_type == DocumentComparisonType.DATES:
        return (
            "Compare datas, prazos, vigencia, vencimentos, renovacao e prazo de pagamento. "
            "Destaque datas adicionadas, removidas ou alteradas."
        )
    if comparison_type == DocumentComparisonType.OBLIGATIONS:
        return (
            "Compare obrigacoes, deveres e responsabilidades das partes. "
            "Indique obrigacoes novas, removidas ou alteradas."
        )
    return (
        "Compare os dois documentos de forma geral. Liste principais diferencas e destaque "
        "alteracoes em clausulas, obrigacoes, prazos, valores e riscos."
    )
