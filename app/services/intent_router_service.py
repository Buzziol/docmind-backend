from app.schemas.agent_schema import AgentDecision, AgentIntent


def classify_intent(message: str) -> AgentDecision:
    normalized = _normalize(message)

    if _contains_any(normalized, EXECUTIVE_SUMMARY_KEYWORDS):
        return AgentDecision(
            intent=AgentIntent.EXECUTIVE_SUMMARY,
            confidence=0.9,
            reason="A mensagem contém termos relacionados a resumo executivo.",
        )

    if _contains_any(normalized, RISK_ANALYSIS_KEYWORDS):
        return AgentDecision(
            intent=AgentIntent.RISK_ANALYSIS,
            confidence=0.9,
            reason="A mensagem contém termos relacionados a riscos ou pontos de atenção.",
        )

    if _contains_any(normalized, DATA_EXTRACTION_KEYWORDS):
        return AgentDecision(
            intent=AgentIntent.DATA_EXTRACTION,
            confidence=0.88,
            reason="A mensagem pede extração de dados estruturados.",
        )

    if _contains_any(normalized, SEMANTIC_SEARCH_KEYWORDS):
        return AgentDecision(
            intent=AgentIntent.SEMANTIC_SEARCH,
            confidence=0.85,
            reason="A mensagem pede explicitamente trechos ou menções nos documentos.",
        )

    return AgentDecision(
        intent=AgentIntent.RAG_QA,
        confidence=0.6,
        reason="Nenhuma intenção específica de análise foi detectada; usando pergunta livre com RAG.",
    )


EXECUTIVE_SUMMARY_KEYWORDS = (
    "resuma",
    "resumo",
    "resumo executivo",
    "sumarizacao",
    "sumarize",
    "principais pontos",
    "pontos principais",
)

RISK_ANALYSIS_KEYWORDS = (
    "risco",
    "riscos",
    "pontos de atencao",
    "clausulas problematicas",
    "exposicao",
    "penalidades",
    "penalidade",
    "multas",
    "multa",
    "obrigacoes sensiveis",
    "pode dar problema",
)

DATA_EXTRACTION_KEYWORDS = (
    "extraia",
    "extrair",
    "extracao",
    "datas",
    "valores",
    "partes",
    "prazos",
    "obrigacoes",
    "penalidades",
    "foro",
    "lei aplicavel",
    "liste datas",
)

SEMANTIC_SEARCH_KEYWORDS = (
    "mostre os trechos",
    "liste os trechos",
    "trechos",
    "onde menciona",
    "quais documentos mencionam",
    "buscar por",
    "busque por",
    "encontre mencoes",
    "menções",
    "mencoes",
)


def _normalize(message: str) -> str:
    return " ".join(message.lower().split())


def _contains_any(message: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in message for keyword in keywords)
