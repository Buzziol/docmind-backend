from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent_routes import router as agent_router
from app.api.routes.analysis_routes import router as analysis_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.chat_routes import router as chat_router
from app.api.routes.dashboard_routes import router as dashboard_router
from app.api.routes.document_chunk_routes import router as document_chunk_router
from app.api.routes.document_comparison_routes import router as document_comparison_router
from app.api.routes.document_embedding_routes import router as document_embedding_router
from app.api.routes.document_processing_routes import router as document_processing_router
from app.api.routes.document_routes import router as document_router
from app.api.routes.health_routes import router as health_router
from app.api.routes.rag_routes import router as rag_router
from app.api.routes.semantic_search_routes import router as semantic_search_router
from app.api.routes.workspace_routes import router as workspace_router
from app.core.config import settings

app = FastAPI(
    title="DocMind API",
    description=(
        "Backend para analise documental inteligente com RAG, preparado para "
        "processar documentos, recuperar contexto e responder com fontes."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(workspace_router, prefix=settings.API_PREFIX)
app.include_router(document_router, prefix=settings.API_PREFIX)
app.include_router(document_processing_router, prefix=settings.API_PREFIX)
app.include_router(document_chunk_router, prefix=settings.API_PREFIX)
app.include_router(document_embedding_router, prefix=settings.API_PREFIX)
app.include_router(semantic_search_router, prefix=settings.API_PREFIX)
app.include_router(rag_router, prefix=settings.API_PREFIX)
app.include_router(analysis_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(agent_router, prefix=settings.API_PREFIX)
app.include_router(document_comparison_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
