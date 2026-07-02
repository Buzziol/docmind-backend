from sqlalchemy.orm import Session

from app.models.analysis_result import AnalysisType
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent_schema import AgentIntent, AgentRequest, AgentResponse
from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.rag_schema import RagQuestionRequest, RagSource
from app.schemas.semantic_search_schema import SemanticSearchRequest
from app.services.analysis_service import run_document_analysis, to_analysis_response
from app.services.chat_history_service import (
    create_assistant_message,
    create_document_chat_session,
    create_user_message,
    create_workspace_chat_session,
)
from app.services.intent_router_service import classify_intent
from app.services.rag_service import answer_document_question, answer_workspace_question
from app.services.semantic_search_service import search_document_chunks, search_workspace_chunks


class AgentError(ValueError):
    pass


def run_document_agent(
    db: Session,
    document: Document,
    user: User,
    request: AgentRequest,
) -> AgentResponse:
    decision = classify_intent(request.message)

    if decision.intent == AgentIntent.RAG_QA:
        rag_response = answer_document_question(
            db,
            document,
            RagQuestionRequest(question=request.message, top_k=min(request.top_k, 10)),
        )
        session = create_document_chat_session(db, user, document, request.message)
        create_user_message(db, session, request.message)
        create_assistant_message(
            db,
            session,
            rag_response.answer,
            [source.model_dump(mode="json") for source in rag_response.sources],
            rag_response.model,
        )
        rag_response.chat_session_id = session.id
        return AgentResponse(
            input=request.message,
            decision=decision,
            result_type="rag_answer",
            result=rag_response.model_dump(mode="json"),
            sources=rag_response.sources,
            chat_session_id=session.id,
            model=rag_response.model,
        )

    if decision.intent == AgentIntent.SEMANTIC_SEARCH:
        search_response = search_document_chunks(
            db,
            document,
            SemanticSearchRequest(query=request.message, top_k=min(request.top_k, 20)),
        )
        sources = [RagSource(**result.model_dump()) for result in search_response.results]
        return AgentResponse(
            input=request.message,
            decision=decision,
            result_type="semantic_search_results",
            result=[result.model_dump(mode="json") for result in search_response.results],
            sources=sources,
        )

    analysis_type = _analysis_type_from_intent(decision.intent)
    analysis = run_document_analysis(
        db,
        document,
        analysis_type,
        AnalysisRequest(force=request.force, top_k=request.top_k),
    )
    analysis_response = to_analysis_response(analysis)
    return AgentResponse(
        input=request.message,
        decision=decision,
        result_type="analysis_result",
        result=analysis_response.model_dump(mode="json"),
        sources=[RagSource(**source.model_dump()) for source in analysis_response.sources],
        analysis_id=analysis.id,
        model=analysis.model,
    )


def run_workspace_agent(
    db: Session,
    workspace: Workspace,
    user: User,
    request: AgentRequest,
) -> AgentResponse:
    decision = classify_intent(request.message)

    if decision.intent in {
        AgentIntent.EXECUTIVE_SUMMARY,
        AgentIntent.RISK_ANALYSIS,
        AgentIntent.DATA_EXTRACTION,
    }:
        raise AgentError("This analysis mode is only available for individual documents")

    if decision.intent == AgentIntent.SEMANTIC_SEARCH:
        search_response = search_workspace_chunks(
            db,
            workspace,
            SemanticSearchRequest(query=request.message, top_k=min(request.top_k, 20)),
        )
        sources = [RagSource(**result.model_dump()) for result in search_response.results]
        return AgentResponse(
            input=request.message,
            decision=decision,
            result_type="semantic_search_results",
            result=[result.model_dump(mode="json") for result in search_response.results],
            sources=sources,
        )

    rag_response = answer_workspace_question(
        db,
        workspace,
        RagQuestionRequest(question=request.message, top_k=min(request.top_k, 10)),
    )
    session = create_workspace_chat_session(db, user, workspace, request.message)
    create_user_message(db, session, request.message)
    create_assistant_message(
        db,
        session,
        rag_response.answer,
        [source.model_dump(mode="json") for source in rag_response.sources],
        rag_response.model,
    )
    rag_response.chat_session_id = session.id
    return AgentResponse(
        input=request.message,
        decision=decision,
        result_type="rag_answer",
        result=rag_response.model_dump(mode="json"),
        sources=rag_response.sources,
        chat_session_id=session.id,
        model=rag_response.model,
    )


def _analysis_type_from_intent(intent: AgentIntent) -> AnalysisType:
    if intent == AgentIntent.EXECUTIVE_SUMMARY:
        return AnalysisType.EXECUTIVE_SUMMARY
    if intent == AgentIntent.RISK_ANALYSIS:
        return AnalysisType.RISK_ANALYSIS
    if intent == AgentIntent.DATA_EXTRACTION:
        return AnalysisType.DATA_EXTRACTION
    raise AgentError("Unsupported analysis intent")
