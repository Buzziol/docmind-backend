from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.rag_schema import RagAnswerResponse, RagQuestionRequest, RagSource
from app.schemas.semantic_search_schema import SemanticSearchRequest
from app.services.llm_service import generate_text
from app.services.semantic_search_service import (
    SemanticSearchError,
    search_document_chunks,
    search_workspace_chunks,
)


class RagError(ValueError):
    pass


def answer_document_question(
    db: Session,
    document: Document,
    question_request: RagQuestionRequest,
) -> RagAnswerResponse:
    search_response = _search_or_raise(
        search_document_chunks(
            db,
            document,
            SemanticSearchRequest(
                query=question_request.question,
                top_k=question_request.top_k,
            ),
        )
    )
    return _build_answer(question_request.question, search_response.results)


def answer_workspace_question(
    db: Session,
    workspace: Workspace,
    question_request: RagQuestionRequest,
) -> RagAnswerResponse:
    search_response = _search_or_raise(
        search_workspace_chunks(
            db,
            workspace,
            SemanticSearchRequest(
                query=question_request.question,
                top_k=question_request.top_k,
            ),
        )
    )
    return _build_answer(question_request.question, search_response.results)


def _search_or_raise(search_response):
    if not search_response.results:
        raise RagError("No embedded chunks found for RAG")
    return search_response


def _build_answer(question: str, search_results) -> RagAnswerResponse:
    sources = [
        RagSource(
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
        for result in search_results
    ]
    context = _build_context(sources)
    prompt = _build_prompt(question, context)
    answer = generate_text(prompt)

    return RagAnswerResponse(
        question=question,
        answer=answer,
        sources=sources,
        model=settings.OLLAMA_MODEL,
        total_sources=len(sources),
    )


def _build_context(sources: list[RagSource]) -> str:
    blocks: list[str] = []
    current_size = 0

    for source in sources:
        block = (
            f"Fonte {len(blocks) + 1}\n"
            f"Documento: {source.document_name}\n"
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


def _build_prompt(question: str, context: str) -> str:
    return f"""Voce e o DocMind, um copiloto de analise documental.
Responda em portugues brasileiro, de forma clara e objetiva.
Use apenas o contexto fornecido abaixo.
Nao invente informacoes.
Se a resposta nao estiver no contexto, diga que nao foi possivel encontrar essa informacao nos documentos fornecidos.
Baseie a resposta nas fontes do contexto.

Contexto:
{context}

Pergunta:
{question}

Resposta:"""
